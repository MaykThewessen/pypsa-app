"""File path validation"""

import logging
from pathlib import Path

from fastapi import HTTPException, status

from pypsa_app.backend.settings import settings

logger = logging.getLogger(__name__)


def validate_path(
    file_path: str | Path, base_dir: Path | None = None, must_exist: bool = False
) -> Path:
    """Validate file path is within base directory (prevents path traversal)"""
    base_dir = base_dir or settings.networks_path

    try:
        path = Path(file_path).resolve()
        base = base_dir.resolve()

        # Check path is within base directory
        path.relative_to(base)  # Raises ValueError otherwise

        if must_exist and not path.exists():
            raise HTTPException(
                status.HTTP_404_NOT_FOUND, f"File not found: {path.name}"
            )

        return path

    except ValueError:
        logger.error(
            "Path traversal attempt detected",
            extra={
                "file_path": str(file_path),
                "base_dir": str(base_dir),
                "resolved_path": str(path) if "path" in locals() else None,
            },
        )
        raise HTTPException(
            status.HTTP_403_FORBIDDEN, "Access denied: Path outside allowed directory"
        )
    except HTTPException:
        raise
