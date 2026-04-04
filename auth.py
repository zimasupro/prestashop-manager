from nicegui import app
from fastapi import Request
from fastapi.responses import RedirectResponse
from starlette.middleware.base import BaseHTTPMiddleware

unrestricted_routes = {"/"}


class AuthMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        if not app.storage.user.get("authenticated", False):
            if request.url.path not in unrestricted_routes:
                return RedirectResponse("/")
        return await call_next(request)
