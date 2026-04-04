from nicegui import ui, events
from dataclasses import dataclass
import pandas as pd
from io import StringIO
from etl.validator import validate
from etl.importer import import_products_csv
from i18n import t


@dataclass
class ImportState:
    clean_df: pd.DataFrame = None
    report: dict = None
    preview: dict = None

    def reset(self):
        self.clean_df = self.report = self.preview = None

    @property
    def ready(self):
        return self.report and self.report["ok"]


def _stats_row(data, keys):
    with ui.row().classes("gap-8 mt-2"):
        for field_name, label, color in keys:
            with ui.column().classes("items-center"):
                ui.label(str(len(data[field_name]))).classes(
                    f"text-3xl font-bold {color}"
                )
                ui.label(label).classes("text-gray-500 text-sm")


def import_tab():
    state = ImportState()

    def handle_cancel():
        state.reset()
        uploader.run_method("reset")
        uploader.set_visibility(True)
        file_row.set_visibility(False)
        current_file.set_text("")
        render_results.refresh()

    @ui.refreshable
    def render_results():
        if not state.report:
            return

        if state.report["fatal"]:
            return

        with ui.card().classes("w-full p-4").style("border-left:4px solid #38a169"):
            if state.report["warnings"]:
                ui.label(t("warnings_title")).classes(
                    "font-semibold text-yellow-600 mb-1"
                )
                for w in state.report["warnings"]:
                    ui.label(f"• {w}").classes("text-yellow-600 text-sm")
            if state.report["cleaned"]:
                ui.label(t("cleaned_title")).classes(
                    "font-semibold text-blue-600 mt-2 mb-1"
                )
                for c in state.report["cleaned"]:
                    ui.label(f"• {c}").classes("text-blue-500 text-sm")
            if not state.report["warnings"] and not state.report["cleaned"]:
                ui.label(t("csv_clean")).classes("text-green-600 font-semibold")

        if not state.ready:
            return

        if not state.preview:
            state.preview = import_products_csv(state.clean_df, dry_run=True)

        with ui.card().classes("w-full p-4 mt-2"):
            ui.label(t("preview_title")).classes("font-semibold mb-2")
            ui.separator()
            _stats_row(
                state.preview,
                [
                    ("to_update", t("to_update"), "text-primary"),
                    ("to_create", t("to_create"), "text-green-600"),
                    ("skipped", t("skipped"), "text-yellow-600"),
                ],
            )
            for s in state.preview["skipped"]:
                ui.label(f"• {s}").classes("text-yellow-600 text-sm mt-1")

        if not state.preview["to_update"] and not state.preview["to_create"]:
            ui.label(t("nothing_to_import")).classes("text-gray-400 mt-2")
            return

        def handle_confirm():
            result = import_products_csv(state.clean_df, dry_run=False)
            with ui.card().classes("w-full p-4 mt-2"):
                label = (
                    t("import_with_errors")
                    if result["errors"]
                    else t("import_complete")
                )
                color = "text-yellow-600" if result["errors"] else "text-green-600"
                ui.label(label).classes(f"font-semibold {color} mb-2")
                _stats_row(
                    result,
                    [
                        ("to_update", t("updated"), "text-primary"),
                        ("to_create", t("created"), "text-green-600"),
                        ("errors", t("errors"), "text-red-500"),
                    ],
                )
                for err in result["errors"]:
                    ui.label(f"• {err}").classes("text-yellow-600 text-sm mt-1")
            action_row.delete()

        with ui.row().classes("w-full justify-between mt-4") as action_row:
            ui.button(t("cancel"), on_click=handle_cancel, icon="close").props(
                "flat dense color=negative"
            )
            ui.button(t("confirm_import"), on_click=handle_confirm).props(
                "color=primary unelevated icon=upload"
            )

    async def handle_upload(e: events.UploadEventArguments) -> None:
        try:
            content = await e.file.read()
            if not content or not content.strip():
                ui.notify(t("file_empty"), type="warning", position="top")
                uploader.run_method("reset")
                return
            try:
                df = pd.read_csv(StringIO(content.decode("utf-8")))
            except pd.errors.EmptyDataError:
                ui.notify(t("file_invalid"), type="warning", position="top")
                uploader.run_method("reset")
                return
            except Exception:
                ui.notify(t("file_parse_error"), type="warning", position="top")
                uploader.run_method("reset")
                return

            state.report, state.clean_df = validate(df)
            state.preview = None
            uploader.run_method("reset")

            if state.report["fatal"]:
                ui.notify(
                    f"⚠️ {e.file.name} {t('file_cant_import')}",
                    type="warning",
                    position="top",
                )
            else:
                uploader.set_visibility(False)
                file_row.set_visibility(True)
                current_file.set_text(f"📄 {e.file.name}")
                ui.notify(
                    f"✅ {e.file.name} {t('file_ready')}",
                    type="positive",
                    position="top",
                )

            render_results.refresh()
        except Exception as ex:
            ui.notify(f"{t('unexpected_error')}: {ex}", type="negative", position="top")

    with ui.column().classes("w-full gap-4"):
        ui.label(t("import_title")).classes("text-lg font-semibold")
        ui.separator()
        ui.label(t("import_subtitle")).classes("text-gray-500 text-sm")
        uploader = (
            ui.upload(
                on_upload=handle_upload, label=t("upload_label"), auto_upload=True
            )
            .classes("w-full")
            .props("accept=.csv flat bordered")
            .style("overflow: hidden;")
        )
        with ui.row().classes("items-center gap-4") as file_row:
            current_file = ui.label("").classes("text-gray-600 text-sm")
        file_row.set_visibility(False)
        render_results()
