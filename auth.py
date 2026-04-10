from nicegui import app
from fastapi import Request
from fastapi.responses import RedirectResponse
from starlette.middleware.base import BaseHTTPMiddleware


unrestricted_routes = {"/", "/setup"}


class AuthMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        path = request.url.path
        is_internal = (
            path.startswith("/_nicegui")
            or path.startswith("/socket.io")
            or path.startswith("/static")
            or path in unrestricted_routes
        )
        if is_internal:
            return await call_next(request)

        if not app.storage.user.get("authenticated", False):
            return RedirectResponse("/")

        presta_configured = app.storage.user.get("presta_url") and app.storage.user.get(
            "presta_api_key"
        )
        if not presta_configured:
            return RedirectResponse("/setup")

        return await call_next(request)
