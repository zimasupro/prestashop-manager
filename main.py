import os
from nicegui import ui, app
from auth import AuthMiddleware
from pages.login import login_page
from pages.dashboard import dashboard_page
from config import STORAGE_SECRET

app.add_middleware(AuthMiddleware)


@ui.page("/")
def index():
    login_page()


@ui.page("/dashboard")
def dashboard():
    dashboard_page()


ui.run(
    host="0.0.0.0",
    port=int(os.environ.get("PORT", 8085)),
    title="PrestaShop Manager",
    storage_secret=STORAGE_SECRET,
    reload=False,
    max_upload_size=50 * 1024 * 1024,
)
