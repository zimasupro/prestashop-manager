from nicegui import ui

from etl.exporter import export_products_csv
from settings import (
    ALWAYS_INCLUDED_FIELDS,
    DEFAULT_EXPORT_FIELDS,
    FLAT_FIELDS,
    MULTILANG_FIELDS,
)
from translator import t


def build_field_options(lang_codes: list) -> list:
    options = []
    for field in MULTILANG_FIELDS:
        for lang in lang_codes:
            options.append(f"{field}_{lang}")
    return options + FLAT_FIELDS


def export_tab(lang_codes: list):
    options = build_field_options(lang_codes)
    selected_fields = {field: field in DEFAULT_EXPORT_FIELDS for field in options}

    ui.label(t("export_title")).classes("text-lg font-semibold")
    ui.label(t("export_subtitle")).classes("text-gray-500 text-sm")
    ui.separator()

    checkboxes = {}
    with ui.column().classes("gap-1 w-full py-2"):
        for field in options:
            checkboxes[field] = ui.checkbox(
                field, value=selected_fields[field]
            ).bind_value(selected_fields, field)

    ui.separator()

    def handle_export():
        selected = ALWAYS_INCLUDED_FIELDS + [f for f, v in selected_fields.items() if v]
        if len(selected) <= len(ALWAYS_INCLUDED_FIELDS):
            ui.notify(t("export_select_one"), type="warning", position="top")
            return
        try:
            path = export_products_csv(fields=selected)
            ui.notify(t("export_success"), type="positive", position="top")
            ui.download(path)
        except Exception as e:
            ui.notify(f"{t('export_failed')}: {e}", type="negative", position="top")

    with ui.row().classes("w-full justify-between items-center mt-2"):
        with ui.row().classes("gap-2"):
            ui.button(
                t("select_all"),
                on_click=lambda: [cb.set_value(True) for cb in checkboxes.values()],
            ).props("flat dense")
            ui.button(
                t("clear"),
                on_click=lambda: [cb.set_value(False) for cb in checkboxes.values()],
            ).props("flat dense")
        ui.button(t("export_button"), on_click=handle_export).props(
            "color=primary unelevated icon=download"
        )
