from fastapi import Request
from fastapi.responses import RedirectResponse
from nicegui import app
from starlette.middleware.base import BaseHTTPMiddleware

from env import APP_PASSWORD, APP_USERNAME

UNRESTRICTED_ROUTES = {"/", "/setup"}

if not APP_USERNAME:
    raise ValueError("APP_USERNAME is required in .env")

if not APP_PASSWORD:
    raise ValueError("APP_PASSWORD is required in .env")


def verify_credentials(username: str, password: str) -> bool:
    return username == APP_USERNAME and password == APP_PASSWORD


def is_authenticated() -> bool:
    return app.storage.user.get("authenticated", False)


def is_presta_configured() -> bool:
    return bool(
        app.storage.user.get("presta_url") and app.storage.user.get("presta_api_key")
    )


def login() -> None:
    app.storage.user["authenticated"] = True


def logout() -> None:
    app.storage.user["authenticated"] = False


class AuthMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        path = request.url.path

        is_passthrough = (
            path.startswith("/_nicegui")
            or path.startswith("/socket.io")
            or path.startswith("/static")
            or path in UNRESTRICTED_ROUTES
        )

        if is_passthrough:
            return await call_next(request)

        if not is_authenticated():
            return RedirectResponse("/")

        if not is_presta_configured():
            return RedirectResponse("/setup")

        return await call_next(request)
