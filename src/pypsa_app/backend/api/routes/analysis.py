"""API routes for custom analysis endpoints (dispatch, line loading, prices, etc.)"""

import logging

from fastapi import APIRouter, Depends, Request, Response
from sqlalchemy.orm import Session

from pypsa_app.backend.api.deps import get_db, get_networks, require_permission
from pypsa_app.backend.api.utils.task_utils import queue_task
from pypsa_app.backend.models import Permission, User
from pypsa_app.backend.ratelimit import limiter
from pypsa_app.backend.schemas.analysis import AnalysisRequest
from pypsa_app.backend.schemas.task import TaskQueuedResponse
from pypsa_app.backend.settings import settings
from pypsa_app.backend.tasks import run_analysis_task

router = APIRouter()
logger = logging.getLogger(__name__)


@router.post("/", response_model=TaskQueuedResponse)
@limiter.limit(settings.ratelimit_expensive)
def create_analysis(
    request: Request,
    response: Response,
    body: AnalysisRequest,
    db: Session = Depends(get_db),
    user: User = Depends(require_permission(Permission.NETWORKS_VIEW)),
) -> dict:
    """Run a custom analysis on one or more networks.

    Available analysis types: dispatch_area, line_loading_histogram,
    line_loading_timeseries, price_duration_curve, price_timeseries,
    cross_border_flows, capacity_mix, nodal_balance, line_flow_snapshot.
    """
    networks = get_networks(db, body.network_ids, user)
    file_paths = [net.file_path for net in networks]

    return queue_task(
        run_analysis_task,
        file_paths=file_paths,
        analysis_type=body.analysis_type,
        parameters=body.parameters,
    )
