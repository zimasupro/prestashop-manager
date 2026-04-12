import os

from fastapi import Response
from fastapi.staticfiles import StaticFiles
from nicegui import app, ui

from authenticator import AuthMiddleware
from env import STORAGE_SECRET
from pages.dashboard import dashboard_page
from pages.login import login_page
from pages.setup import setup_page

if not STORAGE_SECRET:
    raise ValueError("STORAGE_SECRET is required in .env")

app.add_middleware(AuthMiddleware)

if not os.path.isdir("static"):
    raise FileNotFoundError("static directory is required")

if not os.path.isfile("static/manifest.json"):
    raise FileNotFoundError("static/manifest.json is required")

app.mount(
    "/static",
    StaticFiles(directory="static"),
    name="static",
)

ui.add_head_html(
    """
    <meta name="theme-color" content="#1976d2">
    <meta name="mobile-web-app-capable" content="yes">
    <meta name="apple-mobile-web-app-capable" content="yes">
    <link rel="manifest" href="/static/manifest.json">
    """,
    shared=True,
)


@ui.page("/")
def serve_login():
    login_page()


@ui.page("/dashboard")
def serve_dashboard():
    dashboard_page()


@ui.page("/setup")
def serve_setup():
    setup_page()


@app.get("/health")
def check_health():
    return Response("OK", status_code=200)


if __name__ in {"__main__", "__mp_main__"}:
    ui.run(
        host="0.0.0.0",
        port=int(os.environ.get("PORT", 8080)),
        title="PrestaShop Manager",
        storage_secret=STORAGE_SECRET,
        reload=False,
        ws_max_size=16777216,
    )
