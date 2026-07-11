"""API routes for browsing network component types and inline-editing their data.

Static, paginated component data already has a home upstream:
`GET /{network_id}/components/{component_name}` in `routes.networks`
(`schemas.network.ComponentDataResponse`). This module adds what upstream is
missing: an overview of all component types in a network, a paginated view of
their time-varying (per-snapshot) data, and an endpoint to edit static values
in place.
"""

import logging
from typing import Any

import pandas as pd
import pypsa
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from pypsa_app.backend.api.deps import Authorized, get_db, require_network
from pypsa_app.backend.models import Network
from pypsa_app.backend.schemas.components import (
    ComponentListResponse,
    ComponentSummary,
    ComponentTimeseriesResponse,
    ComponentUpdateRequest,
)
from pypsa_app.backend.services.network import (
    NetworkService,
    _apply_network_metadata,
    _calculate_file_hash,
    _network_cache,
)

router = APIRouter()
logger = logging.getLogger(__name__)

# Standard-type components (e.g. LineType) mirror the same catalogue for every
# network and aren't user data, so they're excluded from the browsable list.
EXCLUDED_NAME_SUFFIX = "Type"


def _get_component(n: pypsa.Network, component_name: str) -> pypsa.Components:
    """Look up a component by name or list_name. Raises 404 if not found."""
    try:
        return n.components[component_name]
    except KeyError as exc:
        raise HTTPException(404, f"Component '{component_name}' not found") from exc


def _dynamic_attrs(component: pypsa.Components) -> list[str]:
    """Time-varying attribute names that carry actual per-component overrides.

    `component.dynamic[attr]` always has one row per snapshot, even when no
    override has been set, so "has data" means "has columns", not "has rows".
    """
    return sorted(attr for attr, df in component.dynamic.items() if len(df.columns) > 0)


def _safe_category(component: pypsa.Components) -> str | None:
    """Extract a component's category, handling the common NaN-float case."""
    category = getattr(component, "category", None)
    if isinstance(category, float):  # NaN for everything except standard types
        return None
    return str(category) if category else None


def _sanitize_row(row: pd.Series) -> list[Any]:
    """Convert a DataFrame row to JSON-safe values (NaN/NaT -> None)."""
    return [None if isinstance(v, float) and (v != v) else v for v in row.tolist()]  # noqa: PLR0124


@router.get("/{network_id}/components", response_model=ComponentListResponse)
def list_components(
    auth: Authorized[Network] = Depends(require_network("read")),
) -> ComponentListResponse:
    """List all non-empty component types in a network with counts and attrs."""
    n = NetworkService(auth.model.file_path).n

    components = [
        ComponentSummary(
            name=component.name,
            list_name=component.list_name,
            count=len(component),
            category=_safe_category(component),
            attrs=list(component.static.columns),
            has_dynamic=bool(dynamic_attrs := _dynamic_attrs(component)),
            dynamic_attrs=dynamic_attrs,
        )
        for component in n.components
        if not component.name.endswith(EXCLUDED_NAME_SUFFIX)
    ]
    components.sort(key=lambda summary: summary.count, reverse=True)

    return ComponentListResponse(
        components=components,
        total_components=len(components),
    )


@router.get(
    "/{network_id}/components/{component_name}/timeseries/{attr}",
    response_model=ComponentTimeseriesResponse,
)
def get_component_timeseries(
    component_name: str,
    attr: str,
    auth: Authorized[Network] = Depends(require_network("read")),
    offset: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=5000),
) -> ComponentTimeseriesResponse:
    """Get paginated time-varying data for a specific component attribute."""
    n = NetworkService(auth.model.file_path).n
    component = _get_component(n, component_name)

    if attr not in component.dynamic or len(component.dynamic[attr].columns) == 0:
        raise HTTPException(
            404, f"No time-varying data for '{attr}' in '{component_name}'"
        )

    ts_df = component.dynamic[attr]
    total_snapshots = len(ts_df)
    page = ts_df.iloc[offset : offset + limit]

    return ComponentTimeseriesResponse(
        component=component.name,
        attr=attr,
        columns=[str(c) for c in page.columns],
        index=[str(idx) for idx in page.index],
        data=[_sanitize_row(row) for _, row in page.iterrows()],
        total_snapshots=total_snapshots,
        offset=offset,
        limit=limit,
    )


@router.patch("/{network_id}/components/{component_name}")
def update_component_data(
    component_name: str,
    body: ComponentUpdateRequest,
    auth: Authorized[Network] = Depends(require_network("modify")),
    db: Session = Depends(get_db),
) -> dict:
    """Update static data for specific component rows.

    Loads a fresh (uncached) copy, applies changes, exports to disk, refreshes
    the network's DB metadata (hash/size/dimensions/etc, same as on import) so
    it doesn't go stale, then invalidates the network cache.
    """
    service = NetworkService(auth.model.file_path, use_cache=False)
    n = service.n
    component = _get_component(n, component_name)
    df = component.static

    missing = [idx for idx in body.updates if idx not in df.index]
    if missing:
        raise HTTPException(404, f"Component indices not found: {missing}")

    updated_columns = {col for changes in body.updates.values() for col in changes}
    invalid_columns = updated_columns - set(df.columns)
    if invalid_columns:
        raise HTTPException(400, f"Invalid columns: {sorted(invalid_columns)}")

    changes_count = 0
    for idx, changes in body.updates.items():
        for col, value in changes.items():
            df.at[idx, col] = value
            changes_count += 1

    n.export_to_netcdf(service.file_path)

    file_hash = _calculate_file_hash(service.file_path)
    _apply_network_metadata(auth.model, service.file_path, file_hash)
    db.commit()
    db.refresh(auth.model)

    # No per-key invalidation is exposed on the cache; clear it rather than
    # reach into its internals (its dict/lock are private to NetworkCache).
    _network_cache.clear()

    logger.info(
        "Component data updated",
        extra={
            "network_id": str(auth.model.id),
            "component": component_name,
            "changes_count": changes_count,
            "updated_by": auth.user.username,
        },
    )

    return {"message": f"Updated {changes_count} values in {component_name}"}
