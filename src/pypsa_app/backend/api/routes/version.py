"""
Version information endpoints
"""

import json
from pathlib import Path

import pypsa
from fastapi import APIRouter

from pypsa_app.backend.__version__ import __version__
from pypsa_app.backend.schemas.version import VersionResponse

router = APIRouter()


def get_frontend_version(package_json_path: Path) -> str:
    """Read version from a package.json file"""
    try:
        if package_json_path.exists():
            with open(package_json_path) as f:
                data = json.load(f)
                return data.get("version", "unknown")
    except Exception:
        pass
    return "unknown"


@router.get("/", response_model=VersionResponse)
async def get_version():
    """Get PyPSA and application version information"""

    # Read frontend versions from package.json files
    project_root = Path(__file__).parent.parent.parent.parent.parent.parent
    app_package_path = project_root / "frontend" / "app" / "package.json"
    map_package_path = project_root / "frontend" / "map" / "package.json"

    frontend_app_version = get_frontend_version(app_package_path)
    frontend_map_version = get_frontend_version(map_package_path)

    return {
        "backend_version": __version__,
        "frontend_app_version": frontend_app_version,
        "frontend_map_version": frontend_map_version,
        "pypsa_version": pypsa.__version__,
    }
