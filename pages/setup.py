from nicegui import app, ui

from presta.client import save_presta_credentials, test_presta_connection


def setup_page():
    with ui.column().classes("w-full max-w-lg mx-auto p-8 gap-6"):
        ui.label("⚙️ PrestaShop Setup").classes("text-3xl font-bold")
        ui.label(
            "Enter your PrestaShop API credentials. These are stored in your session."
        ).classes("text-gray-500")

        ui.label("🔒 Server Access").classes(
            "text-sm font-semibold text-gray-400 uppercase tracking-wide"
        )
        http_user_input = ui.input(
            label="Server Username",
            placeholder="HTTP Basic Auth username (if required)",
            value=app.storage.user.get("http_user", ""),
        ).classes("w-full")
        http_pass_input = ui.input(
            label="Server Password",
            placeholder="HTTP Basic Auth password (if required)",
            value=app.storage.user.get("http_pass", ""),
            password=True,
            password_toggle_button=True,
        ).classes("w-full")

        ui.separator()

        ui.label("🛒 PrestaShop Webservice").classes(
            "text-sm font-semibold text-gray-400 uppercase tracking-wide"
        )
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

        def _get_inputs():
            return (
                url_input.value.strip().rstrip("/"),
                key_input.value.strip(),
                http_user_input.value.strip(),
                http_pass_input.value.strip(),
            )

        def _set_status(text, color):
            status.set_text(text)
            status.classes(
                color,
                remove=" ".join(
                    c
                    for c in ["text-green-600", "text-red-600", "text-yellow-600"]
                    if c != color
                ),
            )

        def handle_test():
            url, key, http_user, http_pass = _get_inputs()
            if not url or not key:
                _set_status(
                    "⚠️ PrestaShop URL and API Key are required.", "text-yellow-600"
                )
                return
            result = test_presta_connection(url, key, http_user, http_pass)
            if result["ok"]:
                _set_status(
                    f"✅ Connected — {len(result['value'])} language(s) found.",
                    "text-green-600",
                )
            else:
                _set_status(f"❌ {result['error']}", "text-red-600")

        def handle_save():
            url, key, http_user, http_pass = _get_inputs()
            if not url or not key:
                ui.notify(
                    "PrestaShop URL and API Key are required.",
                    type="warning",
                    position="top",
                )
                return
            result = test_presta_connection(url, key, http_user, http_pass)
            if not result["ok"]:
                _set_status(
                    f"❌ {result['error']} — fix before saving.", "text-red-600"
                )
                return
            save_presta_credentials(url, key, http_user, http_pass)
            ui.notify("✅ Connected! Redirecting...", type="positive", position="top")
            ui.navigate.to("/dashboard")

        with ui.row().classes("gap-3 mt-2"):
            ui.button("Test Connection", on_click=handle_test).props(
                "flat color=primary"
            )
            ui.button("Save & Continue", on_click=handle_save).props(
                "unelevated color=primary"
            )
