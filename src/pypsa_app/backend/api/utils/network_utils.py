"""Network utilities"""

import logging
from pathlib import Path

from sqlalchemy.orm import Session

from pypsa_app.backend.models import Network

logger = logging.getLogger(__name__)


def delete_network(network: Network, db: Session) -> str:
    """Delete network from DB and file system. Returns status message."""
    filename = network.filename
    file_path = Path(network.file_path)

    db.delete(network)
    db.commit()

    if file_path.exists():
        try:
            file_path.unlink()
        except (PermissionError, OSError) as e:
            logger.warning("DB deleted but file remains for %s: %s", filename, e)
        else:
            logger.info("Deleted network file: %s", file_path)
            return f"Network {filename} deleted successfully"

    return f"Network {filename} removed from database (file cleanup may be needed)"
