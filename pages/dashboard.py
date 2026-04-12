from nicegui import ui

from pages.export_tab import export_tab
from pages.import_tab import import_tab
from presta.client import get_languages
from settings import PRIMARY_COLOR
from translator import get_lang, set_lang, t

NAV_ITEMS = [
    ("home", "overview", "Overview"),
    ("upload", "export", "tab_export"),
    ("download", "import", "tab_import"),
    ("analytics", "abcxyz", "ABC-XYZ"),
]


def dashboard_page():
    ui.colors(primary=PRIMARY_COLOR)

    lang_result = get_languages()
    if not lang_result["ok"]:
        with ui.column().classes("w-full max-w-lg mx-auto p-8 gap-4 items-center"):
            ui.icon("cloud_off", size="4rem").classes("text-red-400")
            ui.label("Could not connect to PrestaShop").classes("text-xl font-semibold")
            ui.label(lang_result["error"]).classes("text-sm text-gray-500 text-center")
            ui.button(
                "Re-configure credentials",
                on_click=lambda: ui.navigate.to("/setup"),
            ).props("unelevated color=primary")
        return

    lang_codes = [lang["iso_code"] for lang in lang_result["value"]]
    active_page = {"value": "overview"}

    with ui.header().classes("items-center justify-between px-4").style(
        f"background:{PRIMARY_COLOR}"
    ):
        ui.button(icon="menu", on_click=lambda: drawer.toggle()).props(
            "flat dense color=white"
        )
        ui.label("🛒 PrestaShop Manager").classes("text-white font-bold text-lg")

        @ui.refreshable
        def lang_switcher():
            with ui.row().classes("gap-3 items-center"):
                for code in ["en", "de", "id"]:
                    is_active = get_lang() == code
                    ui.label(code.upper()).classes(
                        "cursor-pointer font-bold text-white underline"
                        if is_active
                        else "cursor-pointer text-white opacity-60 hover:opacity-100"
                    ).on(
                        "click",
                        lambda c=code: (
                            set_lang(c),
                            lang_switcher.refresh(),
                            page_content.refresh(),
                        ),
                    )

        lang_switcher()

    with ui.left_drawer(value=False).classes("bg-white shadow-lg") as drawer:
        ui.label("Menu").classes(
            "text-xs font-semibold text-gray-400 uppercase tracking-wide px-4 pt-4 pb-2"
        )
        ui.separator()
        for icon, key, label in NAV_ITEMS:
            display = (
                label
                if key == "abcxyz"
                else t(label) if label.startswith("tab_") else label
            )
            ui.item(
                display,
                on_click=lambda k=key: (
                    active_page.update({"value": k}),
                    drawer.hide(),
                    page_content.refresh(),
                ),
            ).props(
                f"clickable v-ripple {'active' if active_page['value'] == key else ''}"
            ).classes(
                "text-primary font-semibold" if active_page["value"] == key else ""
            )

    @ui.refreshable
    def page_content():
        page = active_page["value"]
        with ui.column().classes("w-full max-w-5xl mx-auto p-6 gap-6"):
            if page == "overview":
                ui.label("Overview").classes("text-2xl font-bold")
                ui.label(
                    "Coming soon — metrics, health indicators, quick actions."
                ).classes("text-gray-400")

            elif page == "export":
                with ui.card().classes("w-full p-6"):
                    export_tab(lang_codes)

            elif page == "import":
                with ui.card().classes("w-full p-6"):
                    import_tab()

            elif page == "abcxyz":
                ui.label("ABC-XYZ Analysis").classes("text-2xl font-bold")
                ui.label("Coming soon.").classes("text-gray-400")

    ui.notify(t("welcome"), type="positive", position="top")
    page_content()
