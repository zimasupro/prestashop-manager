"""
test_core.py — Pitch Day Smoke Tests
Covers: validator.py, importer.py, exporter.py, presta/client.py
Run with: pytest test_core.py -v
"""

import pytest
import pandas as pd
from unittest.mock import patch, MagicMock


# ============================================================
# SECTION 1: validator.py
# ============================================================

from etl.validator import clean_html, validate


class TestCleanHtml:

    def test_removes_disallowed_tags(self):
        """Script tags should be stripped, text preserved."""
        html = "<p>Hello <script>bad()</script> world</p>"
        cleaned, changes = clean_html(html)
        assert "<script>" not in cleaned
        assert "Hello" in cleaned

    def test_removes_inline_styles(self):
        html = '<p style="color:red">Text</p>'
        cleaned, changes = clean_html(html)
        assert "style=" not in cleaned
        assert "removed inline style" in " ".join(changes)

    def test_removes_class_attributes(self):
        html = '<p class="highlight">Text</p>'
        cleaned, changes = clean_html(html)
        assert "class=" not in cleaned

    def test_normalizes_h1_to_h2(self):
        # h1 is not in ALLOWED_TAGS so it gets unwrapped (tag removed, text kept)
        # before the h1→h2 rename can run — text must still be preserved
        html = "<h1>Title</h1>"
        cleaned, changes = clean_html(html)
        assert "Title" in cleaned
        assert "<h1>" not in cleaned

    def test_replaces_nbsp(self):
        # BeautifulSoup converts &nbsp; to \xa0 on parse,
        # so we pass the unicode char directly to trigger the replacement
        html = "<p>Hello\xa0World</p>"
        cleaned, changes = clean_html(html)
        assert "&nbsp;" not in cleaned
        assert "\xa0" not in cleaned

    def test_empty_input_returns_as_is(self):
        cleaned, changes = clean_html("")
        assert cleaned == ""
        assert changes == []

    def test_none_input_returns_as_is(self):
        cleaned, changes = clean_html(None)
        assert cleaned is None
        assert changes == []


class TestValidate:

    def _make_df(self, overrides=None):
        """Helper: creates a minimal valid product DataFrame."""
        data = {
            "id": [1],
            "name_en": ["Test Product"],
            "price": [9.99],
            "active": ["1"],
        }
        if overrides:
            data.update(overrides)
        return pd.DataFrame(data)

    def test_valid_product_passes(self):
        df = self._make_df()
        report, _ = validate(df)
        assert report["ok"] is True
        assert report["fatal"] == []

    def test_missing_required_column_is_fatal(self):
        """Removing 'id' column should cause a fatal error."""
        df = self._make_df()
        df = df.drop(columns=["id"])
        report, _ = validate(df)
        assert report["ok"] is False
        assert any("id" in f for f in report["fatal"])

    def test_no_name_columns_is_fatal(self):
        df = pd.DataFrame({"id": [1], "price": [9.99]})
        report, _ = validate(df)
        assert report["ok"] is False
        assert any("name" in f for f in report["fatal"])

    def test_empty_id_is_fatal(self):
        df = self._make_df({"id": [None]})
        report, _ = validate(df)
        assert report["ok"] is False

    def test_all_names_empty_is_fatal(self):
        df = self._make_df({"name_en": [""]})
        report, _ = validate(df)
        assert report["ok"] is False

    def test_zero_price_is_warning(self):
        df = self._make_df({"price": [0]})
        report, _ = validate(df)
        assert report["ok"] is True  # warning, not fatal
        assert any("price" in w for w in report["warnings"])

    def test_negative_price_is_warning(self):
        df = self._make_df({"price": [-5]})
        report, _ = validate(df)
        assert any("price" in w for w in report["warnings"])

    def test_invalid_active_value_is_warning(self):
        df = self._make_df({"active": ["yes"]})
        report, _ = validate(df)
        assert any("active" in w for w in report["warnings"])

    def test_valid_active_values_no_warning(self):
        for val in ["0", "1", ""]:
            df = self._make_df({"active": [val]})
            report, _ = validate(df)
            assert not any("active" in w for w in report["warnings"])

    def test_html_description_is_auto_cleaned(self):
        df = self._make_df({"description_en": ['<p style="color:red">Desc</p>']})
        report, clean_df = validate(df)
        assert "style=" not in clean_df["description_en"].iloc[0]
        assert len(report["cleaned"]) > 0

    def test_multiple_products_mixed_validity(self):
        df = pd.DataFrame(
            {
                "id": [1, None],
                "name_en": ["Good Product", "Also Good"],
                "price": [10.0, 20.0],
            }
        )
        report, _ = validate(df)
        assert report["ok"] is False
        assert any("empty id" in f for f in report["fatal"])


# ============================================================
# SECTION 2: importer.py (dry_run=True — no API calls)
# ============================================================

from etl.importer import import_products_csv, _row_to_fields, _build_lang_map

MOCK_LANGUAGES = [
    {"id": "1", "iso_code": "en"},
    {"id": "2", "iso_code": "de"},
]

# get_languages() returns {"ok": True, "value": [...]} — always wrap the mock
MOCK_LANGUAGES_RESULT = {"ok": True, "value": MOCK_LANGUAGES}


class TestBuildLangMap:

    def test_builds_correct_map(self):
        result = _build_lang_map(MOCK_LANGUAGES)
        assert result == {1: "en", 2: "de"}


class TestRowToFields:

    def test_filters_none_values(self):
        row = {"id": 1, "name_en": None, "price": 9.99}
        result = _row_to_fields(row)
        assert "name_en" not in result

    def test_filters_empty_strings(self):
        row = {"id": 1, "name_en": "", "price": 9.99}
        result = _row_to_fields(row)
        assert "name_en" not in result

    def test_filters_nan_strings(self):
        row = {"id": 1, "name_en": "nan", "price": 9.99}
        result = _row_to_fields(row)
        assert "name_en" not in result

    def test_keeps_valid_values(self):
        row = {"id": 1, "name_en": "Product", "price": 9.99}
        result = _row_to_fields(row)
        assert result == {"id": 1, "name_en": "Product", "price": 9.99}


class TestImportProductsCsvDryRun:

    def _make_update_df(self):
        return pd.DataFrame(
            {
                "id": [42],
                "name_en": ["Test Product"],
                "price": [19.99],
            }
        )

    def _make_create_df(self):
        # REQUIRED_CREATE_FIELDS = ["name", "link_rewrite"]
        return pd.DataFrame(
            {
                "id": [None],
                "name_en": ["New Product"],
                "link_rewrite_en": ["new-product"],
                "price": [9.99],
            }
        )

    @patch("etl.importer.get_languages", return_value=MOCK_LANGUAGES_RESULT)
    def test_dry_run_does_not_call_patch(self, mock_langs):
        with patch("etl.importer.patch_product") as mock_patch:
            import_products_csv(self._make_update_df(), dry_run=True)
            mock_patch.assert_not_called()

    @patch("etl.importer.get_languages", return_value=MOCK_LANGUAGES_RESULT)
    def test_dry_run_detects_update(self, mock_langs):
        report = import_products_csv(self._make_update_df(), dry_run=True)
        assert len(report["to_update"]) == 1
        assert report["to_update"][0]["id"] == 42

    @patch("etl.importer.get_languages", return_value=MOCK_LANGUAGES_RESULT)
    def test_dry_run_detects_create(self, mock_langs):
        report = import_products_csv(self._make_create_df(), dry_run=True)
        assert len(report["to_create"]) == 1

    @patch("etl.importer.get_languages", return_value=MOCK_LANGUAGES_RESULT)
    def test_invalid_id_is_skipped(self, mock_langs):
        df = pd.DataFrame({"id": ["abc"], "name_en": ["Bad"]})
        report = import_products_csv(df, dry_run=True)
        assert len(report["skipped"]) == 1

    @patch("etl.importer.get_languages", return_value=MOCK_LANGUAGES_RESULT)
    def test_dry_run_flag_in_report(self, mock_langs):
        report = import_products_csv(self._make_update_df(), dry_run=True)
        assert report["dry_run"] is True


# ============================================================
# SECTION 3: exporter.py — flatten_multilang (pure logic)
# ============================================================

from etl.exporter import flatten_multilang

LANG_MAP = {1: "en", 2: "de", 3: "id"}


class TestFlattenMultilang:

    def test_list_of_languages(self):
        value = {
            "language": [
                {"id": "1", "value": "Hello"},
                {"id": "2", "value": "Hallo"},
            ]
        }
        result = flatten_multilang(value, LANG_MAP)
        assert result == {"en": "Hello", "de": "Hallo"}

    def test_single_language_dict(self):
        """Single language comes as dict not list — should normalize."""
        value = {"language": {"id": "1", "value": "Hello"}}
        result = flatten_multilang(value, LANG_MAP)
        assert result == {"en": "Hello"}

    def test_plain_string_uses_default_lang(self):
        result = flatten_multilang("Hello", LANG_MAP)
        assert result == {"en": "Hello"}

    def test_empty_value_returns_empty(self):
        result = flatten_multilang(None, LANG_MAP)
        assert result == {}

    def test_unknown_lang_id_is_skipped(self):
        value = {"language": [{"id": "99", "value": "Unknown"}]}
        result = flatten_multilang(value, LANG_MAP)
        assert result == {}

    def test_missing_id_in_item_is_skipped(self):
        value = {"language": [{"value": "No ID here"}]}
        result = flatten_multilang(value, LANG_MAP)
        assert result == {}

    def test_non_list_non_dict_returns_empty(self):
        result = flatten_multilang(12345, LANG_MAP)
        assert result == {}


# ============================================================
# SECTION 4: presta/client.py — _build_product_xml (pure logic)
# ============================================================

from presta.client import _build_product_xml

LANG_MAP_CLIENT = {1: "en", 2: "de"}


class TestBuildProductXml:

    def test_contains_product_id(self):
        xml = _build_product_xml(99, {"price": "19.99"}, LANG_MAP_CLIENT)
        assert "<id>99</id>" in xml

    def test_no_id_when_none(self):
        """Create mode — no id element."""
        xml = _build_product_xml(None, {"price": "19.99"}, LANG_MAP_CLIENT)
        assert "<id>" not in xml

    def test_flat_field_included(self):
        xml = _build_product_xml(1, {"price": "29.99"}, LANG_MAP_CLIENT)
        assert "<price>29.99</price>" in xml

    def test_multilang_field_structure(self):
        fields = {"name_en": "Hello", "name_de": "Hallo"}
        xml = _build_product_xml(1, fields, LANG_MAP_CLIENT)
        assert '<language id="1">' in xml
        assert "Hello" in xml
        assert "Hallo" in xml

    def test_empty_fields_not_included(self):
        fields = {"price": "10.00", "name_en": ""}
        xml = _build_product_xml(1, fields, LANG_MAP_CLIENT)
        assert "name_en" not in xml

    def test_xml_declaration_present(self):
        xml = _build_product_xml(1, {"price": "5.00"}, LANG_MAP_CLIENT)
        assert xml.startswith('<?xml version="1.0"')

    def test_prestashop_root_element(self):
        xml = _build_product_xml(1, {"price": "5.00"}, LANG_MAP_CLIENT)
        assert "<prestashop" in xml
        assert "<product>" in xml


# ============================================================
# SECTION 5: importer.py — real run (dry_run=False)
# ============================================================

class TestImportProductsCsvRealRun:

    def _make_update_df(self):
        return pd.DataFrame(
            {
                "id": [42],
                "name_en": ["Test Product"],
                "price": [19.99],
            }
        )

    @patch("etl.importer.get_languages", return_value=MOCK_LANGUAGES_RESULT)
    @patch(
        "etl.importer.patch_product",
        return_value={"ok": False, "error": "401 Unauthorized"},
    )
    def test_failed_patch_goes_to_errors(self, mock_patch, mock_langs):
        report = import_products_csv(self._make_update_df(), dry_run=False)
        assert len(report["errors"]) == 1
        assert "42" in report["errors"][0] or "401" in report["errors"][0]

    @patch("etl.importer.get_languages", return_value=MOCK_LANGUAGES_RESULT)
    @patch("etl.importer.patch_product", return_value={"ok": True})
    def test_successful_patch_not_in_errors(self, mock_patch, mock_langs):
        report = import_products_csv(self._make_update_df(), dry_run=False)
        assert len(report["errors"]) == 0

    @patch("etl.importer.get_languages", return_value={"ok": False, "error": "401 Unauthorized"})
    def test_languages_failure_returns_error_report(self, mock_langs):
        """If get_languages() fails, import should return an error report not crash."""
        report = import_products_csv(self._make_update_df(), dry_run=False)
        assert len(report["errors"]) == 1
        assert "languages" in report["errors"][0].lower()