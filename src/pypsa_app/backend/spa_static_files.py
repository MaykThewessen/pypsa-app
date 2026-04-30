"""Custom StaticFiles handler for SPA (Single Page Application) routing.
Falls back to index.html for client-side routing and allows to serve static files
(from build frontend).
"""

from http import HTTPStatus

from fastapi.staticfiles import StaticFiles
from starlette.exceptions import HTTPException
from starlette.responses import Response
from starlette.types import Scope


class SPAStaticFiles(StaticFiles):
    """Static files for Single Page Application."""

    async def get_response(self, path: str, scope: Scope) -> Response:
        try:
            return await super().get_response(path, scope)
        except HTTPException as ex:
            if ex.status_code == HTTPStatus.NOT_FOUND:
                # Return index.html for all non-file routes
                # This allows SvelteKit's client-side router to handle the route
                return await super().get_response("index.html", scope)
            raise
