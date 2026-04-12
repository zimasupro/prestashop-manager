from nicegui import ui

from authenticator import is_authenticated, login, verify_credentials
from translator import translate as t


def login_page():
    if is_authenticated():
        ui.navigate.to("/dashboard")
        return

    with ui.column().classes("absolute-center items-center gap-4"):
        ui.label(t("app_title")).classes("text-3xl font-bold")
        ui.label(t("login")).classes("text-xl text-gray-500")

        username = ui.input(t("username")).classes("w-64")
        password = ui.input(t("password"), password=True).classes("w-64")

        def handle_login():
            if verify_credentials(username.value, password.value):
                login()
                ui.navigate.to("/dashboard")
            else:
                ui.notify(t("wrong_credentials"), type="negative", position="top")

        ui.button(t("login"), on_click=handle_login).classes("w-64")
