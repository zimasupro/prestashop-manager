from nicegui import ui

from etl.exporter import export_products_csv
from presta.client import get_languages
from settings import (
    ALWAYS_INCLUDED_FIELDS,
    DEFAULT_EXPORT_FIELDS,
    FLAT_FIELDS,
    MULTILANG_FIELDS,
    PRIMARY_COLOR,
)
from translator import get_lang, set_lang, t


def build_field_options(lang_codes):
    options = []
    for field in MULTILANG_FIELDS:
        for lang in lang_codes:
            options.append(f"{field}_{lang}")
    return options + FLAT_FIELDS


def dashboard_page():
    ui.colors(primary=PRIMARY_COLOR)

    # --- GUARDED: unwrap Result from get_languages ---
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

    options = build_field_options(lang_codes)
    selected_fields = {field: field in DEFAULT_EXPORT_FIELDS for field in options}

    ui.notify(t("welcome"), type="positive", position="top")

    with ui.column().classes("w-full max-w-5xl mx-auto p-8 gap-6"):

        @ui.refreshable
        def lang_switcher():
            with ui.row().classes("gap-4 items-center"):
                for code, label in {"en": "EN", "de": "DE", "id": "ID"}.items():
                    is_active = get_lang() == code
                    ui.label(label).classes(
                        "cursor-pointer font-bold underline text-primary"
                        if is_active
                        else "cursor-pointer text-gray-400 hover:text-primary"
                    ).on(
                        "click",
                        lambda c=code: (
                            set_lang(c),
                            lang_switcher.refresh(),
                            page_content.refresh(),
                        ),
                    )

        with ui.row().classes("w-full justify-between items-center"):
            ui.label("🛒 PrestaShop Manager").classes("text-3xl font-bold")
            lang_switcher()

        @ui.refreshable
        def page_content():
            with ui.tabs().classes("w-full") as tabs:
                tab_export = ui.tab(t("tab_export"))
                tab_import = ui.tab(t("tab_import"))

            with ui.tab_panels(tabs, value=tab_export).classes("w-full"):

                with ui.tab_panel(tab_export):
                    with ui.card().classes("w-full p-6").style(
                        "box-shadow: 0 2px 8px rgba(0,0,0,0.10)"
                    ):
                        ui.label(t("export_title")).classes("text-lg font-semibold")
                        ui.separator()

                        checkboxes = {}
                        with ui.column().classes("gap-1 w-full py-2"):
                            for field in options:
                                checkboxes[field] = ui.checkbox(
                                    field, value=selected_fields[field]
                                ).bind_value(selected_fields, field)

                        ui.separator()

                        with ui.row().classes(
                            "w-full justify-between items-center mt-2"
                        ):
                            with ui.row().classes("gap-2"):
                                ui.button(
                                    t("select_all"),
                                    on_click=lambda: [
                                        cb.set_value(True) for cb in checkboxes.values()
                                    ],
                                ).props("flat dense")
                                ui.button(
                                    t("clear"),
                                    on_click=lambda: [
                                        cb.set_value(False)
                                        for cb in checkboxes.values()
                                    ],
                                ).props("flat dense")

                            def handle_export():
                                selected = ALWAYS_INCLUDED_FIELDS + [
                                    f for f, v in selected_fields.items() if v
                                ]
                                if len(selected) <= len(ALWAYS_INCLUDED_FIELDS):
                                    ui.notify(
                                        t("export_select_one"),
                                        type="warning",
                                        position="top",
                                    )
                                    return
                                try:
                                    path = export_products_csv(fields=selected)
                                    ui.notify(
                                        t("export_success"),
                                        type="positive",
                                        position="top",
                                    )
                                    ui.download(path)
                                except Exception as e:
                                    ui.notify(
                                        f"{t('export_failed')}: {e}",
                                        type="negative",
                                        position="top",
                                    )

                            ui.button(t("export_button"), on_click=handle_export).props(
                                "color=primary unelevated icon=download"
                            )

                from pages.import_tab import import_tab

                with ui.tab_panel(tab_import):
                    with ui.card().classes("w-full p-6").style(
                        "box-shadow: 0 2px 8px rgba(0,0,0,0.10)"
                    ):
                        import_tab()

        page_content()
