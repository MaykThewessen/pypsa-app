"""API routes for saved dashboard views."""

import logging
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import or_, select
from sqlalchemy.orm import Session, joinedload

from pypsa_app.backend.api.deps import get_db, require_permission
from pypsa_app.backend.api.pagination import (
    PaginationParams,
    apply_pagination,
    list_meta,
)
from pypsa_app.backend.models import Permission, SavedView, User, Visibility
from pypsa_app.backend.permissions import has_permission
from pypsa_app.backend.schemas.common import MessageResponse
from pypsa_app.backend.schemas.views import (
    SavedViewCreate,
    SavedViewListResponse,
    SavedViewResponse,
    SavedViewUpdate,
)

router = APIRouter()
logger = logging.getLogger(__name__)


def _get_view_or_404(view_id: UUID, db: Session) -> SavedView:
    """Fetch a saved view by ID with its owner eager-loaded, or 404."""
    view = db.scalars(
        select(SavedView)
        .options(joinedload(SavedView.owner))
        .where(SavedView.id == view_id)
    ).first()
    if not view:
        raise HTTPException(404, "View not found")
    return view


@router.post("/", response_model=SavedViewResponse, status_code=201)
def create_view(
    body: SavedViewCreate,
    db: Session = Depends(get_db),
    user: User = Depends(require_permission(Permission.NETWORKS_MODIFY)),
) -> SavedView:
    """Create a new saved dashboard view."""
    view = SavedView(
        user_id=user.id,
        network_id=body.network_id,
        name=body.name,
        description=body.description,
        visibility=body.visibility,
        config=body.config.model_dump(),
    )
    db.add(view)
    db.commit()
    db.refresh(view)

    logger.info(
        "Saved view created",
        extra={
            "view_id": str(view.id),
            "view_name": view.name,
            "user": user.username,
        },
    )
    return view


@router.get("/", response_model=SavedViewListResponse)
def list_views(
    params: PaginationParams = Depends(),
    network_id: UUID | None = Query(None, description="Filter by network ID"),
    db: Session = Depends(get_db),
    user: User = Depends(require_permission(Permission.NETWORKS_VIEW)),
) -> SavedViewListResponse:
    """List saved views accessible to the current user."""
    query = select(SavedView).options(joinedload(SavedView.owner))

    # Users see their own views + public views; admins see everything.
    if not has_permission(user, Permission.NETWORKS_MANAGE_ALL):
        query = query.where(
            or_(
                SavedView.user_id == user.id,
                SavedView.visibility == Visibility.PUBLIC,
            )
        )

    if network_id is not None:
        query = query.where(
            or_(
                SavedView.network_id == network_id,
                SavedView.network_id.is_(None),  # Global views apply to any network
            )
        )

    views_query, total = apply_pagination(
        query,
        SavedView,
        params,
        session=db,
        allowed_sort_fields={"created_at", "updated_at", "name"},
        default_sort="updated_at",
    )
    views = db.scalars(views_query).all()

    return SavedViewListResponse(data=views, meta=list_meta(total, params, len(views)))


@router.get("/{view_id}", response_model=SavedViewResponse)
def get_view(
    view_id: UUID,
    db: Session = Depends(get_db),
    user: User = Depends(require_permission(Permission.NETWORKS_VIEW)),
) -> SavedView:
    """Get a saved view by ID."""
    view = _get_view_or_404(view_id, db)

    # Check access: own views, public views, or admin.
    if (
        view.user_id != user.id
        and view.visibility != Visibility.PUBLIC
        and not has_permission(user, Permission.NETWORKS_MANAGE_ALL)
    ):
        raise HTTPException(404, "View not found")

    return view


@router.patch("/{view_id}", response_model=SavedViewResponse)
def update_view(
    view_id: UUID,
    body: SavedViewUpdate,
    db: Session = Depends(get_db),
    user: User = Depends(require_permission(Permission.NETWORKS_MODIFY)),
) -> SavedView:
    """Update a saved view. Only the owner (or an admin) can update."""
    view = _get_view_or_404(view_id, db)

    if view.user_id != user.id and not has_permission(
        user, Permission.NETWORKS_MANAGE_ALL
    ):
        raise HTTPException(403, "You can only update your own views")

    if body.name is not None:
        view.name = body.name
    if body.description is not None:
        view.description = body.description
    if body.visibility is not None:
        view.visibility = body.visibility
    if body.config is not None:
        view.config = body.config.model_dump()

    db.commit()
    db.refresh(view)
    return view


@router.delete("/{view_id}", response_model=MessageResponse)
def delete_view(
    view_id: UUID,
    db: Session = Depends(get_db),
    user: User = Depends(require_permission(Permission.NETWORKS_MODIFY)),
) -> dict:
    """Delete a saved view. Only the owner (or an admin) can delete."""
    view = db.scalars(select(SavedView).where(SavedView.id == view_id)).first()
    if not view:
        raise HTTPException(404, "View not found")

    if view.user_id != user.id and not has_permission(
        user, Permission.NETWORKS_MANAGE_ALL
    ):
        raise HTTPException(403, "You can only delete your own views")

    db.delete(view)
    db.commit()

    logger.info(
        "Saved view deleted", extra={"view_id": str(view_id), "user": user.username}
    )
    return {"message": "View deleted"}
