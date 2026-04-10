from nicegui import ui, app
import requests
from requests.auth import HTTPBasicAuth


def setup_page():
    with ui.column().classes("w-full max-w-lg mx-auto p-8 gap-6"):
        ui.label("⚙️ PrestaShop Setup").classes("text-3xl font-bold")
        ui.label(
            "Enter your PrestaShop API credentials. These are stored in your session."
        ).classes("text-gray-500")

        url_input = ui.input(
            label="PrestaShop URL",
            placeholder="https://yourstore.com/api",
            value=app.storage.user.get("presta_url", ""),
        ).classes("w-full")

        key_input = ui.input(
            label="API Key",
            placeholder="Your PrestaShop API key",
            value=app.storage.user.get("presta_api_key", ""),
            password=True,
            password_toggle_button=True,
        ).classes("w-full")

        status = ui.label("").classes("text-sm")

        def test_connection():
            url = url_input.value.strip().rstrip("/")
            key = key_input.value.strip()
            if not url or not key:
                status.set_text("⚠️ Both fields are required.")
                status.classes("text-yellow-600", remove="text-green-600 text-red-600")
                return
            try:
                r = requests.get(
                    f"{url}/languages",
                    auth=HTTPBasicAuth(key, ""),
                    params={"output_format": "JSON", "display": "full"},
                    timeout=8,
                )
                r.raise_for_status()
                langs = r.json().get("languages", [])
                status.set_text(f"✅ Connected — {len(langs)} language(s) found.")
                status.classes("text-green-600", remove="text-yellow-600 text-red-600")
            except Exception as e:
                status.set_text(f"❌ Connection failed: {e}")
                status.classes("text-red-600", remove="text-yellow-600 text-green-600")

        def save_and_continue():
            url = url_input.value.strip().rstrip("/")
            key = key_input.value.strip()
            if not url or not key:
                ui.notify("Both fields are required.", type="warning", position="top")
                return
            app.storage.user["presta_url"] = url
            app.storage.user["presta_api_key"] = key
            ui.navigate.to("/dashboard")

        with ui.row().classes("gap-3 mt-2"):
            ui.button("Test Connection", on_click=test_connection).props(
                "flat color=primary"
            )
            ui.button("Save & Continue", on_click=save_and_continue).props(
                "unelevated color=primary"
            )
