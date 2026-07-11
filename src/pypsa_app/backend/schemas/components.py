"""Schemas for network component browsing and inline editing.

Static component data (`GET /{network_id}/components/{component_name}`) is
already served by `schemas.network.ComponentDataResponse`; the schemas here
cover the capabilities upstream lacks: the component type overview, the
time-varying (per-snapshot) data view, and the inline-edit request body.
"""

from typing import Any

from pydantic import BaseModel


class ComponentSummary(BaseModel):
    """Summary of a single network component type."""

    name: str
    list_name: str
    count: int
    category: str | None = None
    attrs: list[str] = []
    has_dynamic: bool = False
    dynamic_attrs: list[str] = []


class ComponentListResponse(BaseModel):
    """List of all component types present in a network."""

    components: list[ComponentSummary]
    total_components: int


class ComponentTimeseriesResponse(BaseModel):
    """Paginated time-varying data for a component attribute."""

    component: str
    attr: str
    columns: list[str]
    index: list[str]
    data: list[list[Any]]
    total_snapshots: int
    offset: int
    limit: int


class ComponentUpdateRequest(BaseModel):
    """Request body for inline-editing static component rows."""

    updates: dict[str, dict[str, Any]]
    """Mapping of component index (e.g. a generator name) -> {column: new_value}."""
