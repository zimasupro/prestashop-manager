"""
test_client.py — Guarded Shell Integration Tests
Tests every failure mode of presta/client.py boundary functions.
Run with: pytest test_client.py -v
"""

import pytest
from unittest.mock import patch, MagicMock
from requests.exceptions import Timeout, ConnectionError
from requests import HTTPError


# ─────────────────────────────────────────────
# Shared fixtures
# ─────────────────────────────────────────────

MOCK_CREDS = ("https://shop.example.com", MagicMock())

MOCK_LANGUAGES_RESPONSE = {
    "languages": [
        {"id": "1", "iso_code": "en"},
        {"id": "2", "iso_code": "de"},
    ]
}

MOCK_PRODUCTS_RESPONSE = {
    "products": [
        {"id": "1"},
        {"id": "2"},
    ]
}

MOCK_PRODUCT_RESPONSE = {"product": {"id": "1", "price": "19.99"}}


def make_http_error(status_code: int):
    """Helper: creates a realistic HTTPError with a given status code."""
    response = MagicMock()
    response.status_code = status_code
    error = HTTPError(response=response)
    return error


# ─────────────────────────────────────────────
# SECTION 1: get_languages()
# ─────────────────────────────────────────────


class TestGetLanguages:

    @patch("presta.client._get", return_value=MOCK_LANGUAGES_RESPONSE)
    def test_returns_languages_on_success(self, mock_get):
        from presta.client import get_languages

        result = get_languages()
        assert result["ok"] is True
        assert len(result["value"]) == 2

    @patch("presta.client._get", return_value={"languages": []})
    def test_empty_languages_returns_error(self, mock_get):
        from presta.client import get_languages

        result = get_languages()
        assert result["ok"] is False
        assert "No languages" in result["error"]

    @patch("presta.client._get", side_effect=Timeout())
    def test_timeout_returns_error(self, mock_get):
        from presta.client import get_languages

        result = get_languages()
        assert result["ok"] is False
        assert "timeout" in result["error"].lower()

    @patch("presta.client._get", side_effect=ConnectionError())
    def test_connection_error_returns_error(self, mock_get):
        from presta.client import get_languages

        result = get_languages()
        assert result["ok"] is False
        assert "reach" in result["error"].lower()

    @patch("presta.client._get", side_effect=make_http_error(401))
    def test_401_returns_auth_error(self, mock_get):
        from presta.client import get_languages

        result = get_languages()
        assert result["ok"] is False
        assert "401" in result["error"]

    @patch("presta.client._get", side_effect=make_http_error(500))
    def test_500_returns_server_error(self, mock_get):
        from presta.client import get_languages

        result = get_languages()
        assert result["ok"] is False
        assert "500" in result["error"]


# ─────────────────────────────────────────────
# SECTION 2: get_products()
# ─────────────────────────────────────────────


class TestGetProducts:

    def _mock_response(self, json_data, status=200):
        mock = MagicMock()
        mock.status_code = status
        mock.json.return_value = json_data
        mock.raise_for_status = MagicMock()
        return mock

    @patch("presta.client._creds", return_value=MOCK_CREDS)
    @patch("requests.get")
    def test_returns_products_on_success(self, mock_get, mock_creds):
        from presta.client import get_products

        mock_get.return_value = self._mock_response(MOCK_PRODUCTS_RESPONSE)
        result = get_products()
        assert result["ok"] is True
        assert len(result["value"]) == 2

    @patch("presta.client._creds", return_value=MOCK_CREDS)
    @patch("requests.get")
    def test_empty_catalog_returns_error(self, mock_get, mock_creds):
        from presta.client import get_products

        mock_get.return_value = self._mock_response({"products": []})
        result = get_products()
        assert result["ok"] is False
        assert "empty" in result["error"].lower()

    @patch("presta.client._creds", return_value=MOCK_CREDS)
    @patch("requests.get", side_effect=Timeout())
    def test_timeout_returns_error(self, mock_get, mock_creds):
        from presta.client import get_products

        result = get_products()
        assert result["ok"] is False
        assert "timeout" in result["error"].lower()

    @patch("presta.client._creds", return_value=MOCK_CREDS)
    @patch("requests.get", side_effect=ConnectionError())
    def test_connection_error_returns_error(self, mock_get, mock_creds):
        from presta.client import get_products

        result = get_products()
        assert result["ok"] is False
        assert "reach" in result["error"].lower()

    @patch(
        "presta.client._creds",
        side_effect=RuntimeError(
            "PrestaShop credentials not configured. Go to /setup."
        ),
    )
    def test_missing_credentials_returns_error(self, mock_creds):
        from presta.client import get_products

        result = get_products()
        assert result["ok"] is False
        assert "credentials" in result["error"].lower()


# ─────────────────────────────────────────────
# SECTION 3: get_product()
# ─────────────────────────────────────────────


class TestGetProduct:

    @patch("presta.client._get", return_value=MOCK_PRODUCT_RESPONSE)
    def test_returns_product_on_success(self, mock_get):
        from presta.client import get_product

        result = get_product(1)
        assert result["ok"] is True
        assert result["value"]["id"] == "1"

    @patch("presta.client._get", return_value={"product": {}})
    def test_empty_product_returns_error(self, mock_get):
        from presta.client import get_product

        result = get_product(999)
        assert result["ok"] is False
        assert "not found" in result["error"].lower()

    @patch("presta.client._get", side_effect=make_http_error(404))
    def test_404_returns_not_found_error(self, mock_get):
        from presta.client import get_product

        result = get_product(999)
        assert result["ok"] is False
        assert "404" in result["error"]

    @patch("presta.client._get", side_effect=Timeout())
    def test_timeout_returns_error(self, mock_get):
        from presta.client import get_product

        result = get_product(1)
        assert result["ok"] is False
        assert "timeout" in result["error"].lower()


# ─────────────────────────────────────────────
# SECTION 4: patch_product() and create_product()
# ─────────────────────────────────────────────

LANG_MAP = {1: "en", 2: "de"}
SAMPLE_FIELDS = {"name_en": "Test", "price": "19.99"}


class TestPatchProduct:

    @patch("presta.client._patch", return_value="<prestashop/>")
    def test_returns_ok_on_success(self, mock_patch):
        from presta.client import patch_product

        result = patch_product(1, SAMPLE_FIELDS, LANG_MAP)
        assert result["ok"] is True

    @patch("presta.client._patch", side_effect=make_http_error(401))
    def test_401_returns_auth_error(self, mock_patch):
        from presta.client import patch_product

        result = patch_product(1, SAMPLE_FIELDS, LANG_MAP)
        assert result["ok"] is False
        assert "401" in result["error"]

    @patch("presta.client._patch", side_effect=Timeout())
    def test_timeout_returns_error(self, mock_patch):
        from presta.client import patch_product

        result = patch_product(1, SAMPLE_FIELDS, LANG_MAP)
        assert result["ok"] is False
        assert "timeout" in result["error"].lower()

    @patch("presta.client._patch", side_effect=make_http_error(500))
    def test_500_returns_server_error(self, mock_patch):
        from presta.client import patch_product

        result = patch_product(1, SAMPLE_FIELDS, LANG_MAP)
        assert result["ok"] is False
        assert "500" in result["error"]


class TestCreateProduct:

    @patch("presta.client._post", return_value="<prestashop/>")
    def test_returns_ok_on_success(self, mock_post):
        from presta.client import create_product

        result = create_product(SAMPLE_FIELDS, LANG_MAP)
        assert result["ok"] is True

    @patch("presta.client._post", side_effect=make_http_error(403))
    def test_403_returns_permission_error(self, mock_post):
        from presta.client import create_product

        result = create_product(SAMPLE_FIELDS, LANG_MAP)
        assert result["ok"] is False
        assert "403" in result["error"]

    @patch("presta.client._post", side_effect=ConnectionError())
    def test_connection_error_returns_error(self, mock_post):
        from presta.client import create_product

        result = create_product(SAMPLE_FIELDS, LANG_MAP)
        assert result["ok"] is False
        assert "reach" in result["error"].lower()


# ─────────────────────────────────────────────
# SECTION 5: _handle_exception() — the error classifier
# ─────────────────────────────────────────────


class TestHandleException:
    """
    Tests the error classifier directly.
    Every HTTP status code and exception type must map
    to a human readable message — no raw exceptions ever reach the UI.
    """

    def setup_method(self):
        from presta.client import _handle_exception

        self.handle = _handle_exception

    def test_timeout_message(self):
        result = self.handle(Timeout())
        assert result["ok"] is False
        assert "timeout" in result["error"].lower()

    def test_connection_error_message(self):
        result = self.handle(ConnectionError())
        assert result["ok"] is False
        assert "reach" in result["error"].lower()

    def test_401_message(self):
        result = self.handle(make_http_error(401))
        assert "401" in result["error"]
        assert "key" in result["error"].lower()

    def test_403_message(self):
        result = self.handle(make_http_error(403))
        assert "403" in result["error"]

    def test_404_message(self):
        result = self.handle(make_http_error(404))
        assert "404" in result["error"]

    def test_500_message(self):
        result = self.handle(make_http_error(500))
        assert "500" in result["error"]

    def test_runtime_error_passes_message_through(self):
        result = self.handle(RuntimeError("credentials not configured"))
        assert result["ok"] is False
        assert "credentials" in result["error"].lower()

    def test_unknown_exception_returns_generic_message(self):
        result = self.handle(Exception("something weird"))
        assert result["ok"] is False
        assert "Unexpected" in result["error"]
