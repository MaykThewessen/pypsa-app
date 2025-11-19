"""
Custom StaticFiles handler for SPA (Single Page Application) routing.
Falls back to index.html for client-side routing and allows to serve static files
(from build frontend).
"""

from fastapi.staticfiles import StaticFiles
from starlette.exceptions import HTTPException


class SPAStaticFiles(StaticFiles):
    """
    Static files for Single Page Application.
    """

    async def get_response(self, path: str, scope):
        try:
            return await super().get_response(path, scope)
        except HTTPException as ex:
            if ex.status_code == 404:
                # Return index.html for all non-file routes
                # This allows SvelteKit's client-side router to handle the route
                return await super().get_response("index.html", scope)
            raise
