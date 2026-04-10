from nicegui import ui, app
from fastapi.staticfiles import StaticFiles
import os


def init_pwa():
    # --- 1. Only mount static if it exists ---
    if os.path.isdir("static"):
        try:
            app.mount("/static", StaticFiles(directory="static"), name="static")
        except RuntimeError:
            # Already mounted (can happen on reloads)
            pass

    # --- 2. Only add manifest if file exists ---
    manifest_exists = os.path.isfile("static/manifest.json")

    head_html = """
        <meta name="theme-color" content="#1976d2">
        <meta name="mobile-web-app-capable" content="yes">
        <meta name="apple-mobile-web-app-capable" content="yes">
    """

    if manifest_exists:
        head_html += '<link rel="manifest" href="/static/manifest.json">'

    # --- 3. Always safe with ui.page ---
    try:
        ui.add_head_html(head_html, shared=True)
    except Exception:
        # Absolute fallback (shouldn't happen, but just in case)
        pass
