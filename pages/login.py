from nicegui import ui, app
from config import APP_USERNAME, APP_PASSWORD
from i18n import t


def login_page():
    if app.storage.user.get("authenticated", False):
        ui.navigate.to("/dashboard")
        return

    with ui.column().classes("absolute-center items-center gap-4"):
        ui.label(t("app_title")).classes("text-3xl font-bold")
        ui.label(t("login")).classes("text-xl text-gray-500")

        username = ui.input(t("username")).classes("w-64")
        password = ui.input(t("password"), password=True).classes("w-64")

        def handle_login():
            if username.value == APP_USERNAME and password.value == APP_PASSWORD:
                app.storage.user["authenticated"] = True
                ui.navigate.to("/dashboard")
            else:
                ui.notify(t("wrong_credentials"), type="negative", position="top")

        ui.button(t("login"), on_click=handle_login).classes("w-64")
