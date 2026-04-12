# App theme
PRIMARY_COLOR = "#E8622A"
APP_TITLE = "PrestaShop Manager"
APP_PORT = 8085

# Export defaults
DEFAULT_EXPORT_FIELDS = ["name_en", "price", "reference"]
ALWAYS_INCLUDED_FIELDS = ["id"]

# Field definitions
MULTILANG_FIELDS = [
    "name",
    "description",
    "description_short",
    "meta_title",
    "meta_description",
    "meta_keywords",
    "link_rewrite",
]

FLAT_FIELDS = [
    "price",
    "wholesale_price",
    "quantity",
    "reference",
    "active",
]

COLUMN_ORDER = [
    "id",
    "reference",
    "name_en",
    "name_de",
    "name_id",
    "description_en",
    "description_de",
    "description_id",
    "description_short_en",
    "description_short_de",
    "description_short_id",
    "meta_title_en",
    "meta_title_de",
    "meta_title_id",
    "meta_description_en",
    "meta_description_de",
    "meta_description_id",
    "meta_keywords_en",
    "meta_keywords_de",
    "meta_keywords_id",
    "link_rewrite_en",
    "link_rewrite_de",
    "link_rewrite_id",
    "price",
    "wholesale_price",
    "quantity",
    "active",
]

REQUIRED_CREATE_FIELDS = [
    "name",
    "link_rewrite",
]

DESCRIPTION_FIELDS = [
    "description",
    "description_short",
]

REQUIRED_FIELDS = ["id"]

ALLOWED_TAGS = {"p", "br", "strong", "em", "ul", "ol", "li", "h2", "h3", "a"}

TRANSLATIONS = {
    "en": {
        # general
        "app_title": "PrestaShop Manager",
        "welcome": "Welcome back! ✅",
        # login
        "login": "Login",
        "username": "Username",
        "password": "Password",
        "wrong_credentials": "Wrong credentials!",
        # tabs
        "tab_export": "📤 Export",
        "tab_import": "📥 Import",
        # export
        "export_title": "Export Products",
        "export_subtitle": "Select fields to export",
        "select_all": "Select All",
        "clear": "Clear",
        "export_button": "Export to CSV",
        "export_success": "Export successful! ✅",
        "export_failed": "Export failed",
        "export_select_one": "Select at least one field.",
        "export_presta_failed": "Failed to connect to PrestaShop",
        # import
        "import_title": "Import Products",
        "import_subtitle": "Upload your edited CSV. We'll validate, preview, then push.",
        "upload_label": "Upload CSV",
        "file_empty": "⚠️ File is empty.",
        "file_invalid": "⚠️ File has no columns — is this a valid CSV?",
        "file_parse_error": "⚠️ Could not parse file — make sure it's a CSV.",
        "file_cant_import": "can't be imported — check your columns",
        "file_ready": "ready",
        "warnings_title": "⚠️ Warnings",
        "cleaned_title": "🧹 Auto-cleaned",
        "csv_clean": "✅ CSV looks clean — ready to import",
        "preview_title": "📋 Import Preview",
        "to_update": "to update",
        "to_create": "to create",
        "skipped": "skipped",
        "nothing_to_import": "Nothing to import.",
        "cancel": "Cancel",
        "confirm_import": "Confirm & Import",
        "import_complete": "✅ Import complete",
        "import_with_errors": "⚠️ Completed with errors",
        "updated": "updated",
        "created": "created",
        "errors": "errors",
        "unexpected_error": "Unexpected error",
    },
    "de": {
        # general
        "app_title": "PrestaShop Manager",
        "welcome": "Willkommen zurück! ✅",
        # login
        "login": "Anmelden",
        "username": "Benutzername",
        "password": "Passwort",
        "wrong_credentials": "Falsche Anmeldedaten!",
        # tabs
        "tab_export": "📤 Exportieren",
        "tab_import": "📥 Importieren",
        # export
        "export_title": "Produkte exportieren",
        "export_subtitle": "Felder zum Exportieren auswählen",
        "select_all": "Alle auswählen",
        "clear": "Löschen",
        "export_button": "Als CSV exportieren",
        "export_success": "Export erfolgreich! ✅",
        "export_failed": "Export fehlgeschlagen",
        "export_select_one": "Mindestens ein Feld auswählen.",
        "export_presta_failed": "Verbindung zu PrestaShop fehlgeschlagen",
        # import
        "import_title": "Produkte importieren",
        "import_subtitle": "Laden Sie Ihre bearbeitete CSV hoch. Wir prüfen, zeigen eine Vorschau und übertragen dann.",
        "upload_label": "CSV hochladen",
        "file_empty": "⚠️ Datei ist leer.",
        "file_invalid": "⚠️ Datei hat keine Spalten — ist das eine gültige CSV?",
        "file_parse_error": "⚠️ Datei konnte nicht gelesen werden — bitte CSV prüfen.",
        "file_cant_import": "kann nicht importiert werden — Spalten prüfen",
        "file_ready": "bereit",
        "warnings_title": "⚠️ Warnungen",
        "cleaned_title": "🧹 Automatisch bereinigt",
        "csv_clean": "✅ CSV sieht gut aus — bereit zum Importieren",
        "preview_title": "📋 Import-Vorschau",
        "to_update": "zu aktualisieren",
        "to_create": "zu erstellen",
        "skipped": "übersprungen",
        "nothing_to_import": "Nichts zu importieren.",
        "cancel": "Abbrechen",
        "confirm_import": "Bestätigen & Importieren",
        "import_complete": "✅ Import abgeschlossen",
        "import_with_errors": "⚠️ Abgeschlossen mit Fehlern",
        "updated": "aktualisiert",
        "created": "erstellt",
        "errors": "Fehler",
        "unexpected_error": "Unerwarteter Fehler",
    },
    "id": {
        # general
        "app_title": "PrestaShop Manager",
        "welcome": "Selamat datang kembali! ✅",
        # login
        "login": "Masuk",
        "username": "Nama Pengguna",
        "password": "Kata Sandi",
        "wrong_credentials": "Kredensial salah!",
        # tabs
        "tab_export": "📤 Ekspor",
        "tab_import": "📥 Impor",
        # export
        "export_title": "Ekspor Produk",
        "export_subtitle": "Pilih kolom yang akan diekspor",
        "select_all": "Pilih Semua",
        "clear": "Hapus",
        "export_button": "Ekspor ke CSV",
        "export_success": "Ekspor berhasil! ✅",
        "export_failed": "Ekspor gagal",
        "export_select_one": "Pilih setidaknya satu kolom.",
        "export_presta_failed": "Gagal terhubung ke PrestaShop",
        # import
        "import_title": "Impor Produk",
        "import_subtitle": "Unggah CSV yang telah diedit. Kami akan memvalidasi, pratinjau, lalu mendorong.",
        "upload_label": "Unggah CSV",
        "file_empty": "⚠️ File kosong.",
        "file_invalid": "⚠️ File tidak memiliki kolom — apakah ini CSV yang valid?",
        "file_parse_error": "⚠️ File tidak dapat dibaca — pastikan formatnya CSV.",
        "file_cant_import": "tidak dapat diimpor — periksa kolom Anda",
        "file_ready": "siap",
        "warnings_title": "⚠️ Peringatan",
        "cleaned_title": "🧹 Dibersihkan otomatis",
        "csv_clean": "✅ CSV terlihat bersih — siap diimpor",
        "preview_title": "📋 Pratinjau Impor",
        "to_update": "akan diperbarui",
        "to_create": "akan dibuat",
        "skipped": "dilewati",
        "nothing_to_import": "Tidak ada yang diimpor.",
        "cancel": "Batal",
        "confirm_import": "Konfirmasi & Impor",
        "import_complete": "✅ Impor selesai",
        "import_with_errors": "⚠️ Selesai dengan kesalahan",
        "updated": "diperbarui",
        "created": "dibuat",
        "errors": "kesalahan",
        "unexpected_error": "Kesalahan tidak terduga",
    },
}

DEFAULT_LANGUAGE = "de"
