import os
from nicegui import ui, app
from auth import AuthMiddleware
from pages.login import login_page
from pages.dashboard import dashboard_page
from config import STORAGE_SECRET
from pages.setup import setup_page

app.add_middleware(AuthMiddleware)


@ui.page("/")
def index():
    login_page()


@ui.page("/dashboard")
def dashboard():
    dashboard_page()

    @ui.page("/setup")
    def setup():
        setup_page()


if __name__ in {"__main__", "__mp_main__"}:
    ui.run(
        host="0.0.0.0",
        port=int(os.environ.get("PORT", 8080)),
        title="PrestaShop Manager",
        storage_secret=STORAGE_SECRET,
        reload=False,
        ws_max_size=16777216,
    )
