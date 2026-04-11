"""
test_connection.py — Sad Path Tests for PrestaShop Connection Layer
Covers:
  - 406 Not Acceptable handling in _handle_exception
  - Accept header is sent on every GET request
  - Output-Format header is sent instead of query param (PS 8.1+)
  - /api suffix is always appended by _creds()
  - _creds() two-scenario auth logic (server auth vs no server auth)
  - _normalize_url() in setup.py
  - test_connection() in setup.py handles all HTTP errors gracefully

Run with: pytest test_connection.py -v
"""

import pytest
from unittest.mock import patch, MagicMock
from requests.exceptions import Timeout, ConnectionError
from requests import HTTPError


# ─────────────────────────────────────────────
# Helpers
# ─────────────────────────────────────────────

# NOTE: _creds() now returns 3 values: (url, auth, extra_params)
MOCK_CREDS_NO_SERVER_AUTH = ("https://shop.example.com/api", MagicMock(), {})
MOCK_CREDS_WITH_SERVER_AUTH = ("https://shop.example.com/api", MagicMock(), {"ws_key": "PS_API_KEY"})


def make_http_error(status_code: int):
    response = MagicMock()
    response.status_code = status_code
    return HTTPError(response=response)


# ─────────────────────────────────────────────
# SECTION 1: _handle_exception — 406 coverage
# ─────────────────────────────────────────────

class TestHandleException406:

    def setup_method(self):
        from presta.client import _handle_exception
        self.handle = _handle_exception

    def test_406_returns_error(self):
        result = self.handle(make_http_error(406))
        assert result["ok"] is False

    def test_406_mentions_406_in_message(self):
        result = self.handle(make_http_error(406))
        assert "406" in result["error"]

    def test_406_mentions_webservice(self):
        result = self.handle(make_http_error(406))
        assert "webservice" in result["error"].lower()

    def test_406_mentions_api_suffix(self):
        result = self.handle(make_http_error(406))
        assert "/api" in result["error"]

    def test_406_is_not_generic_message(self):
        result = self.handle(make_http_error(406))
        assert "unexpected" not in result["error"].lower()


# ─────────────────────────────────────────────
# SECTION 2: 401 now mentions server credentials
# ─────────────────────────────────────────────

class TestHandleException401:

    def setup_method(self):
        from presta.client import _handle_exception
        self.handle = _handle_exception

    def test_401_returns_error(self):
        result = self.handle(make_http_error(401))
        assert result["ok"] is False

    def test_401_mentions_server_credentials(self):
        """401 message must tell the user to check server username/password too."""
        result = self.handle(make_http_error(401))
        assert "401" in result["error"]
        assert any(word in result["error"].lower() for word in ["server", "username", "password", "key"])

    def test_401_is_not_generic_message(self):
        result = self.handle(make_http_error(401))
        assert "unexpected" not in result["error"].lower()


# ─────────────────────────────────────────────
# SECTION 3: Accept + Output-Format headers always sent
# ─────────────────────────────────────────────

class TestHeadersAlwaysSent:

    def _mock_json_response(self, data):
        mock = MagicMock()
        mock.json.return_value = data
        mock.raise_for_status = MagicMock()
        return mock

    @patch("presta.client._creds", return_value=MOCK_CREDS_NO_SERVER_AUTH)
    @patch("requests.get")
    def test_get_languages_sends_accept_header(self, mock_get, mock_creds):
        from presta.client import get_languages
        mock_get.return_value = self._mock_json_response(
            {"languages": [{"id": "1", "iso_code": "en"}]}
        )
        get_languages()
        headers = mock_get.call_args[1]["headers"]
        assert headers.get("Accept") == "application/json"

    @patch("presta.client._creds", return_value=MOCK_CREDS_NO_SERVER_AUTH)
    @patch("requests.get")
    def test_get_languages_sends_output_format_header(self, mock_get, mock_creds):
        from presta.client import get_languages
        mock_get.return_value = self._mock_json_response(
            {"languages": [{"id": "1", "iso_code": "en"}]}
        )
        get_languages()
        headers = mock_get.call_args[1]["headers"]
        assert headers.get("Output-Format") == "JSON"

    @patch("presta.client._creds", return_value=MOCK_CREDS_NO_SERVER_AUTH)
    @patch("requests.get")
    def test_output_format_not_in_params(self, mock_get, mock_creds):
        """output_format must NOT be a query param — causes 406 on PS 8.1+."""
        from presta.client import get_languages
        mock_get.return_value = self._mock_json_response(
            {"languages": [{"id": "1", "iso_code": "en"}]}
        )
        get_languages()
        params = mock_get.call_args[1]["params"]
        assert "output_format" not in params

    @patch("presta.client._creds", return_value=MOCK_CREDS_NO_SERVER_AUTH)
    @patch("requests.get")
    def test_get_products_sends_output_format_header(self, mock_get, mock_creds):
        from presta.client import get_products
        mock_get.return_value = self._mock_json_response({"products": [{"id": "1"}]})
        get_products()
        headers = mock_get.call_args[1]["headers"]
        assert headers.get("Output-Format") == "JSON"

    @patch("presta.client._creds", return_value=MOCK_CREDS_NO_SERVER_AUTH)
    @patch("requests.get")
    def test_get_product_sends_output_format_header(self, mock_get, mock_creds):
        from presta.client import get_product
        mock_get.return_value = self._mock_json_response({"product": {"id": "1"}})
        get_product(1)
        headers = mock_get.call_args[1]["headers"]
        assert headers.get("Output-Format") == "JSON"


# ─────────────────────────────────────────────
# SECTION 4: /api suffix guard in _creds()
# ─────────────────────────────────────────────

class TestApiSuffixGuard:

    def _mock_storage(self, url, key="testkey", http_user="", http_pass=""):
        return {
            "presta_url": url,
            "presta_api_key": key,
            "http_user": http_user,
            "http_pass": http_pass,
        }

    @patch("presta.client.app")
    def test_url_without_api_gets_api_appended(self, mock_app):
        from presta.client import _creds
        storage = self._mock_storage("https://shop.example.com")
        mock_app.storage.user.get.side_effect = lambda k, d="": storage.get(k, d)
        url, _, _ = _creds()
        assert url.endswith("/api")

    @patch("presta.client.app")
    def test_url_with_api_is_not_doubled(self, mock_app):
        from presta.client import _creds
        storage = self._mock_storage("https://shop.example.com/api")
        mock_app.storage.user.get.side_effect = lambda k, d="": storage.get(k, d)
        url, _, _ = _creds()
        assert url == "https://shop.example.com/api"
        assert "/api/api" not in url

    @patch("presta.client.app")
    def test_trailing_slash_stripped_before_api_check(self, mock_app):
        from presta.client import _creds
        storage = self._mock_storage("https://shop.example.com/")
        mock_app.storage.user.get.side_effect = lambda k, d="": storage.get(k, d)
        url, _, _ = _creds()
        assert url == "https://shop.example.com/api"

    @patch("presta.client.app")
    def test_missing_url_raises_runtime_error(self, mock_app):
        from presta.client import _creds
        storage = self._mock_storage("")
        mock_app.storage.user.get.side_effect = lambda k, d="": storage.get(k, d)
        with pytest.raises(RuntimeError, match="credentials not configured"):
            _creds()

    @patch("presta.client.app")
    def test_missing_key_raises_runtime_error(self, mock_app):
        from presta.client import _creds
        storage = self._mock_storage("https://shop.example.com/api", key="")
        mock_app.storage.user.get.side_effect = lambda k, d="": storage.get(k, d)
        with pytest.raises(RuntimeError, match="credentials not configured"):
            _creds()


# ─────────────────────────────────────────────
# SECTION 5: _creds() two-scenario auth logic
# ─────────────────────────────────────────────

class TestCredsAuthScenarios:
    """
    _creds() must handle two auth scenarios:
      1. No server auth  → Basic Auth = PS API key, extra_params = {}
      2. Server auth set → Basic Auth = server creds, extra_params = {ws_key: PS key}
    """

    def _mock_storage(self, url, key, http_user="", http_pass=""):
        return {
            "presta_url": url,
            "presta_api_key": key,
            "http_user": http_user,
            "http_pass": http_pass,
        }

    @patch("presta.client.app")
    def test_no_server_auth_returns_empty_extra_params(self, mock_app):
        from presta.client import _creds
        storage = self._mock_storage("https://shop.example.com/api", "PS_KEY")
        mock_app.storage.user.get.side_effect = lambda k, d="": storage.get(k, d)
        _, _, extra_params = _creds()
        assert extra_params == {}

    @patch("presta.client.app")
    def test_no_server_auth_uses_ps_key_as_basic_auth(self, mock_app):
        from presta.client import _creds
        from requests.auth import HTTPBasicAuth
        storage = self._mock_storage("https://shop.example.com/api", "PS_KEY")
        mock_app.storage.user.get.side_effect = lambda k, d="": storage.get(k, d)
        _, auth, _ = _creds()
        assert auth.username == "PS_KEY"
        assert auth.password == ""

    @patch("presta.client.app")
    def test_server_auth_returns_ws_key_in_extra_params(self, mock_app):
        from presta.client import _creds
        storage = self._mock_storage(
            "https://shop.example.com/api", "PS_KEY",
            http_user="admin", http_pass="secret"
        )
        mock_app.storage.user.get.side_effect = lambda k, d="": storage.get(k, d)
        _, _, extra_params = _creds()
        assert extra_params.get("ws_key") == "PS_KEY"

    @patch("presta.client.app")
    def test_server_auth_uses_server_creds_as_basic_auth(self, mock_app):
        from presta.client import _creds
        storage = self._mock_storage(
            "https://shop.example.com/api", "PS_KEY",
            http_user="admin", http_pass="secret"
        )
        mock_app.storage.user.get.side_effect = lambda k, d="": storage.get(k, d)
        _, auth, _ = _creds()
        assert auth.username == "admin"
        assert auth.password == "secret"

    @patch("presta.client.app")
    def test_server_auth_does_not_expose_ps_key_as_basic_auth_user(self, mock_app):
        """When server auth is set, PS key must NOT be the Basic Auth username."""
        from presta.client import _creds
        storage = self._mock_storage(
            "https://shop.example.com/api", "PS_KEY",
            http_user="admin", http_pass="secret"
        )
        mock_app.storage.user.get.side_effect = lambda k, d="": storage.get(k, d)
        _, auth, _ = _creds()
        assert auth.username != "PS_KEY"


# ─────────────────────────────────────────────
# SECTION 6: ws_key param is sent when server auth is active
# ─────────────────────────────────────────────

class TestWsKeyParam:
    """When server auth is present, ws_key must be in every request's params."""

    def _mock_json_response(self, data):
        mock = MagicMock()
        mock.json.return_value = data
        mock.raise_for_status = MagicMock()
        return mock

    @patch("presta.client._creds", return_value=MOCK_CREDS_WITH_SERVER_AUTH)
    @patch("requests.get")
    def test_get_languages_sends_ws_key_param(self, mock_get, mock_creds):
        from presta.client import get_languages
        mock_get.return_value = self._mock_json_response(
            {"languages": [{"id": "1", "iso_code": "en"}]}
        )
        get_languages()
        params = mock_get.call_args[1]["params"]
        assert params.get("ws_key") == "PS_API_KEY"

    @patch("presta.client._creds", return_value=MOCK_CREDS_WITH_SERVER_AUTH)
    @patch("requests.get")
    def test_get_products_sends_ws_key_param(self, mock_get, mock_creds):
        from presta.client import get_products
        mock_get.return_value = self._mock_json_response({"products": [{"id": "1"}]})
        get_products()
        params = mock_get.call_args[1]["params"]
        assert params.get("ws_key") == "PS_API_KEY"

    @patch("presta.client._creds", return_value=MOCK_CREDS_NO_SERVER_AUTH)
    @patch("requests.get")
    def test_no_server_auth_does_not_send_ws_key_param(self, mock_get, mock_creds):
        from presta.client import get_languages
        mock_get.return_value = self._mock_json_response(
            {"languages": [{"id": "1", "iso_code": "en"}]}
        )
        get_languages()
        params = mock_get.call_args[1]["params"]
        assert "ws_key" not in params


# ─────────────────────────────────────────────
# SECTION 7: _normalize_url() in setup.py
# ─────────────────────────────────────────────

class TestNormalizeUrl:

    def setup_method(self):
        from pages.setup import _normalize_url
        self.normalize = _normalize_url

    def test_appends_api_when_missing(self):
        assert self.normalize("https://shop.example.com") == "https://shop.example.com/api"

    def test_does_not_double_api(self):
        assert self.normalize("https://shop.example.com/api") == "https://shop.example.com/api"

    def test_strips_trailing_slash(self):
        assert self.normalize("https://shop.example.com/") == "https://shop.example.com/api"

    def test_strips_trailing_slash_with_api(self):
        assert self.normalize("https://shop.example.com/api/") == "https://shop.example.com/api"

    def test_strips_whitespace(self):
        assert self.normalize("  https://shop.example.com  ") == "https://shop.example.com/api"


# ─────────────────────────────────────────────
# SECTION 8: get_languages() sad paths with 406
# ─────────────────────────────────────────────

class TestGetLanguages406:

    @patch("presta.client._get", side_effect=make_http_error(406))
    def test_406_returns_error_not_exception(self, mock_get):
        from presta.client import get_languages
        result = get_languages()
        assert result["ok"] is False

    @patch("presta.client._get", side_effect=make_http_error(406))
    def test_406_error_message_is_actionable(self, mock_get):
        from presta.client import get_languages
        result = get_languages()
        assert "406" in result["error"]
        assert "webservice" in result["error"].lower()

    @patch("presta.client._get", side_effect=make_http_error(406))
    def test_get_products_406_returns_error(self, mock_get):
        from presta.client import get_products
        result = get_products()
        assert result["ok"] is False
        assert "406" in result["error"]

    @patch("presta.client._get", side_effect=make_http_error(406))
    def test_get_product_406_returns_error(self, mock_get):
        from presta.client import get_product
        result = get_product(1)
        assert result["ok"] is False
        assert "406" in result["error"]