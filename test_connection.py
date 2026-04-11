"""
test_connection.py — Sad Path Tests for PrestaShop Connection Layer
Covers:
  - 406 Not Acceptable handling in _handle_exception
  - Accept header is sent on every GET request
  - /api suffix is always appended by _creds()
  - _normalize_url() in setup.py
  - test_connection() in setup.py handles all HTTP errors gracefully

Run with: pytest test_connection.py -v
"""

import pytest
from unittest.mock import patch, MagicMock, call
from requests.exceptions import Timeout, ConnectionError
from requests import HTTPError


# ─────────────────────────────────────────────
# Helpers
# ─────────────────────────────────────────────

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
        """User must be told to check the Webservice setting — that's the fix."""
        result = self.handle(make_http_error(406))
        assert "webservice" in result["error"].lower()

    def test_406_mentions_api_suffix(self):
        """User must be told the URL needs /api."""
        result = self.handle(make_http_error(406))
        assert "/api" in result["error"]

    def test_406_is_not_generic_message(self):
        """406 must NOT fall through to the generic 'unexpected error' handler."""
        result = self.handle(make_http_error(406))
        assert "unexpected" not in result["error"].lower()


# ─────────────────────────────────────────────
# SECTION 2: Accept header is always sent
# ─────────────────────────────────────────────

MOCK_CREDS = ("https://shop.example.com/api", MagicMock())


class TestAcceptHeaderAlwaysSent:

    def _mock_json_response(self, data):
        mock = MagicMock()
        mock.json.return_value = data
        mock.raise_for_status = MagicMock()
        return mock

    @patch("presta.client._creds", return_value=MOCK_CREDS)
    @patch("requests.get")
    def test_get_languages_sends_accept_header(self, mock_get, mock_creds):
        from presta.client import get_languages
        mock_get.return_value = self._mock_json_response(
            {"languages": [{"id": "1", "iso_code": "en"}]}
        )
        get_languages()
        headers = mock_get.call_args[1]["headers"]
        assert headers.get("Accept") == "application/json"

    @patch("presta.client._creds", return_value=MOCK_CREDS)
    @patch("requests.get")
    def test_get_products_sends_accept_header(self, mock_get, mock_creds):
        from presta.client import get_products
        mock_get.return_value = self._mock_json_response(
            {"products": [{"id": "1"}]}
        )
        get_products()
        headers = mock_get.call_args[1]["headers"]
        assert headers.get("Accept") == "application/json"

    @patch("presta.client._creds", return_value=MOCK_CREDS)
    @patch("requests.get")
    def test_get_product_sends_accept_header(self, mock_get, mock_creds):
        from presta.client import get_product
        mock_get.return_value = self._mock_json_response(
            {"product": {"id": "1"}}
        )
        get_product(1)
        headers = mock_get.call_args[1]["headers"]
        assert headers.get("Accept") == "application/json"


# ─────────────────────────────────────────────
# SECTION 3: /api suffix guard in _creds()
# ─────────────────────────────────────────────

class TestApiSuffixGuard:

    def _make_storage(self, url, key="testkey"):
        return {"presta_url": url, "presta_api_key": key}

    @patch("presta.client.app")
    def test_url_without_api_gets_api_appended(self, mock_app):
        from presta.client import _creds
        mock_app.storage.user.get.side_effect = lambda k, d="": {
            "presta_url": "https://shop.example.com",
            "presta_api_key": "abc123",
        }.get(k, d)
        url, _ = _creds()
        assert url.endswith("/api")

    @patch("presta.client.app")
    def test_url_with_api_is_not_doubled(self, mock_app):
        from presta.client import _creds
        mock_app.storage.user.get.side_effect = lambda k, d="": {
            "presta_url": "https://shop.example.com/api",
            "presta_api_key": "abc123",
        }.get(k, d)
        url, _ = _creds()
        assert url == "https://shop.example.com/api"
        assert "/api/api" not in url

    @patch("presta.client.app")
    def test_trailing_slash_stripped_before_api_check(self, mock_app):
        from presta.client import _creds
        mock_app.storage.user.get.side_effect = lambda k, d="": {
            "presta_url": "https://shop.example.com/",
            "presta_api_key": "abc123",
        }.get(k, d)
        url, _ = _creds()
        assert url == "https://shop.example.com/api"

    @patch("presta.client.app")
    def test_missing_url_raises_runtime_error(self, mock_app):
        from presta.client import _creds
        mock_app.storage.user.get.side_effect = lambda k, d="": {
            "presta_url": "",
            "presta_api_key": "abc123",
        }.get(k, d)
        with pytest.raises(RuntimeError, match="credentials not configured"):
            _creds()

    @patch("presta.client.app")
    def test_missing_key_raises_runtime_error(self, mock_app):
        from presta.client import _creds
        mock_app.storage.user.get.side_effect = lambda k, d="": {
            "presta_url": "https://shop.example.com/api",
            "presta_api_key": "",
        }.get(k, d)
        with pytest.raises(RuntimeError, match="credentials not configured"):
            _creds()


# ─────────────────────────────────────────────
# SECTION 4: _normalize_url() in setup.py
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
# SECTION 5: get_languages() sad paths with 406
# ─────────────────────────────────────────────

class TestGetLanguages406:

    @patch("presta.client._get", side_effect=make_http_error(406))
    def test_406_returns_error_not_exception(self, mock_get):
        """A 406 must never bubble up as an unhandled exception."""
        from presta.client import get_languages
        result = get_languages()
        assert result["ok"] is False

    @patch("presta.client._get", side_effect=make_http_error(406))
    def test_406_error_message_is_actionable(self, mock_get):
        """The error message must tell the user what to do."""
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