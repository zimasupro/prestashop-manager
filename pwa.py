from nicegui import ui, app
from fastapi.staticfiles import StaticFiles


def init_pwa():
    app.mount("/static", StaticFiles(directory="static"), name="static")

    ui.add_head_html(
        """
        <link rel="manifest" href="/static/manifest.json">
        <meta name="theme-color" content="#1976d2">
        <meta name="mobile-web-app-capable" content="yes">
        <meta name="apple-mobile-web-app-capable" content="yes">
    """
    )
