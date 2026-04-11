"""
test_client.py — Guarded Shell Integration Tests
Tests every failure mode of presta/client.py boundary functions.
Run with: pytest test_client.py -v
"""

import pytest
from unittest.mock import patch, MagicMock
from requests.exceptions import Timeout, ConnectionError
from requests import HTTPError

# NOTE: _creds() now returns 3 values: (url, auth, extra_params)
MOCK_CREDS = ("https://shop.example.com/api", MagicMock(), {})
MOCK_CREDS_WITH_SERVER_AUTH = ("https://shop.example.com/api", MagicMock(), {"ws_key": "PS_API_KEY"})

MOCK_LANGUAGES_RESPONSE = {"languages": [{"id": "1", "iso_code": "en"}, {"id": "2", "iso_code": "de"}]}
MOCK_PRODUCTS_RESPONSE = {"products": [{"id": "1"}, {"id": "2"}]}
MOCK_PRODUCT_RESPONSE = {"product": {"id": "1", "price": "19.99"}}


def make_http_error(status_code: int):
    response = MagicMock()
    response.status_code = status_code
    return HTTPError(response=response)


def mock_response(json_data):
    mock = MagicMock()
    mock.json.return_value = json_data
    mock.raise_for_status = MagicMock()
    return mock


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


class TestGetProducts:

    @patch("presta.client._get", return_value=MOCK_PRODUCTS_RESPONSE)
    def test_returns_products_on_success(self, mock_get):
        from presta.client import get_products
        result = get_products()
        assert result["ok"] is True
        assert len(result["value"]) == 2

    @patch("presta.client._get", return_value={"products": []})
    def test_empty_catalog_returns_error(self, mock_get):
        from presta.client import get_products
        result = get_products()
        assert result["ok"] is False
        assert "empty" in result["error"].lower()

    @patch("presta.client._get", side_effect=Timeout())
    def test_timeout_returns_error(self, mock_get):
        from presta.client import get_products
        result = get_products()
        assert result["ok"] is False
        assert "timeout" in result["error"].lower()

    @patch("presta.client._creds", side_effect=RuntimeError("PrestaShop credentials not configured. Go to /setup."))
    def test_missing_credentials_returns_error(self, mock_creds):
        from presta.client import get_products
        result = get_products()
        assert result["ok"] is False
        assert "credentials" in result["error"].lower()

    @patch("presta.client._creds", return_value=MOCK_CREDS)
    @patch("requests.get")
    def test_get_products_sends_limit_zero(self, mock_get, mock_creds):
        from presta.client import get_products
        mock_get.return_value = mock_response(MOCK_PRODUCTS_RESPONSE)
        get_products()
        assert mock_get.call_args[1]["params"].get("limit") == "0"


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

    @patch("presta.client._creds", return_value=MOCK_CREDS)
    @patch("requests.get")
    def test_get_product_uses_display_full(self, mock_get, mock_creds):
        from presta.client import get_product
        mock_get.return_value = mock_response(MOCK_PRODUCT_RESPONSE)
        get_product(1)
        assert mock_get.call_args[1]["params"].get("display") == "full"


LANG_MAP = {1: "en", 2: "de"}
SAMPLE_FIELDS = {"name_en": "Test", "price": "19.99"}


class TestPatchProduct:

    @patch("presta.client._patch", return_value="<prestashop/>")
    def test_returns_ok_on_success(self, mock_patch):
        from presta.client import patch_product
        assert patch_product(1, SAMPLE_FIELDS, LANG_MAP)["ok"] is True

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


class TestCreateProduct:

    @patch("presta.client._post", return_value="<prestashop/>")
    def test_returns_ok_on_success(self, mock_post):
        from presta.client import create_product
        assert create_product(SAMPLE_FIELDS, LANG_MAP)["ok"] is True

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


class TestHandleException:

    def setup_method(self):
        from presta.client import _handle_exception
        self.handle = _handle_exception

    def test_timeout_message(self):
        assert "timeout" in self.handle(Timeout())["error"].lower()

    def test_connection_error_message(self):
        assert "reach" in self.handle(ConnectionError())["error"].lower()

    def test_401_mentions_server_credentials(self):
        result = self.handle(make_http_error(401))
        assert "401" in result["error"]
        assert any(w in result["error"].lower() for w in ["server", "username", "password", "key"])

    def test_403_message(self):
        assert "403" in self.handle(make_http_error(403))["error"]

    def test_404_message(self):
        assert "404" in self.handle(make_http_error(404))["error"]

    def test_406_message(self):
        result = self.handle(make_http_error(406))
        assert "406" in result["error"]
        assert "webservice" in result["error"].lower()

    def test_500_message(self):
        assert "500" in self.handle(make_http_error(500))["error"]

    def test_runtime_error_passes_through(self):
        result = self.handle(RuntimeError("credentials not configured"))
        assert "credentials" in result["error"].lower()

    def test_unknown_exception_generic_message(self):
        assert "Unexpected" in self.handle(Exception("weird"))["error"]


class TestServerAuthFlow:
    """ws_key must appear in params for GET, PATCH, POST when server auth is active."""

    @patch("presta.client._creds", return_value=MOCK_CREDS_WITH_SERVER_AUTH)
    @patch("requests.get")
    def test_get_sends_ws_key(self, mock_get, mock_creds):
        from presta.client import get_languages
        mock_get.return_value = mock_response({"languages": [{"id": "1", "iso_code": "en"}]})
        get_languages()
        assert mock_get.call_args[1]["params"].get("ws_key") == "PS_API_KEY"

    @patch("presta.client._creds", return_value=MOCK_CREDS_WITH_SERVER_AUTH)
    @patch("requests.patch")
    def test_patch_sends_ws_key(self, mock_patch, mock_creds):
        from presta.client import patch_product
        mock_patch.return_value = mock_response("<prestashop/>")
        mock_patch.return_value.text = "<prestashop/>"
        patch_product(1, {"price": "9.99"}, {1: "en"})
        assert mock_patch.call_args[1]["params"].get("ws_key") == "PS_API_KEY"

    @patch("presta.client._creds", return_value=MOCK_CREDS_WITH_SERVER_AUTH)
    @patch("requests.post")
    def test_post_sends_ws_key(self, mock_post, mock_creds):
        from presta.client import create_product
        mock_post.return_value = mock_response("<prestashop/>")
        mock_post.return_value.text = "<prestashop/>"
        create_product({"price": "9.99"}, {1: "en"})
        assert mock_post.call_args[1]["params"].get("ws_key") == "PS_API_KEY"

    @patch("presta.client._creds", return_value=MOCK_CREDS)
    @patch("requests.get")
    def test_no_server_auth_no_ws_key(self, mock_get, mock_creds):
        from presta.client import get_languages
        mock_get.return_value = mock_response({"languages": [{"id": "1", "iso_code": "en"}]})
        get_languages()
        assert "ws_key" not in mock_get.call_args[1]["params"]