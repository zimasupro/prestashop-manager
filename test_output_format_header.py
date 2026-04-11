"""
test_output_format_header.py — Verifies PS 8.1+ Output-Format header behaviour
PrestaShop 8.1+ requires `Output-Format: JSON` as a request header.
Sending `output_format=JSON` as a query param causes a 406.

Run with: pytest test_output_format_header.py -v
"""

import pytest
from unittest.mock import patch, MagicMock


MOCK_CREDS = ("https://shop.example.com/api", MagicMock())


def mock_json_response(data):
    mock = MagicMock()
    mock.json.return_value = data
    mock.raise_for_status = MagicMock()
    return mock


# ─────────────────────────────────────────────
# SECTION 1: Output-Format header is sent, not query param
# ─────────────────────────────────────────────

class TestOutputFormatHeader:
    """
    PS 9 / 8.1+ refuses output_format=JSON as a query param (returns 406).
    The fix: send Output-Format: JSON as a request header instead.
    """

    @patch("presta.client._creds", return_value=MOCK_CREDS)
    @patch("requests.get")
    def test_get_languages_sends_output_format_header(self, mock_get, mock_creds):
        """Output-Format must be in headers, not params."""
        from presta.client import get_languages
        mock_get.return_value = mock_json_response(
            {"languages": [{"id": "1", "iso_code": "en"}]}
        )
        get_languages()
        headers = mock_get.call_args[1]["headers"]
        assert headers.get("Output-Format") == "JSON"

    @patch("presta.client._creds", return_value=MOCK_CREDS)
    @patch("requests.get")
    def test_get_languages_does_not_send_output_format_as_param(self, mock_get, mock_creds):
        """output_format must NOT appear as a query param — that causes 406 on PS 9."""
        from presta.client import get_languages
        mock_get.return_value = mock_json_response(
            {"languages": [{"id": "1", "iso_code": "en"}]}
        )
        get_languages()
        params = mock_get.call_args[1]["params"]
        assert "output_format" not in params

    @patch("presta.client._creds", return_value=MOCK_CREDS)
    @patch("requests.get")
    def test_get_products_sends_output_format_header(self, mock_get, mock_creds):
        from presta.client import get_products
        mock_get.return_value = mock_json_response(
            {"products": [{"id": "1"}]}
        )
        get_products()
        headers = mock_get.call_args[1]["headers"]
        assert headers.get("Output-Format") == "JSON"

    @patch("presta.client._creds", return_value=MOCK_CREDS)
    @patch("requests.get")
    def test_get_products_does_not_send_output_format_as_param(self, mock_get, mock_creds):
        from presta.client import get_products
        mock_get.return_value = mock_json_response(
            {"products": [{"id": "1"}]}
        )
        get_products()
        params = mock_get.call_args[1]["params"]
        assert "output_format" not in params

    @patch("presta.client._creds", return_value=MOCK_CREDS)
    @patch("requests.get")
    def test_get_product_sends_output_format_header(self, mock_get, mock_creds):
        from presta.client import get_product
        mock_get.return_value = mock_json_response(
            {"product": {"id": "1"}}
        )
        get_product(1)
        headers = mock_get.call_args[1]["headers"]
        assert headers.get("Output-Format") == "JSON"

    @patch("presta.client._creds", return_value=MOCK_CREDS)
    @patch("requests.get")
    def test_accept_header_still_present(self, mock_get, mock_creds):
        """Both Accept and Output-Format must be sent together."""
        from presta.client import get_languages
        mock_get.return_value = mock_json_response(
            {"languages": [{"id": "1", "iso_code": "en"}]}
        )
        get_languages()
        headers = mock_get.call_args[1]["headers"]
        assert headers.get("Accept") == "application/json"
        assert headers.get("Output-Format") == "JSON"


# ─────────────────────────────────────────────
# SECTION 2: JSON_HEADERS constant is correct
# ─────────────────────────────────────────────

class TestJsonHeadersConstant:

    def test_json_headers_contains_output_format(self):
        from presta.client import JSON_HEADERS
        assert JSON_HEADERS.get("Output-Format") == "JSON"

    def test_json_headers_contains_accept(self):
        from presta.client import JSON_HEADERS
        assert JSON_HEADERS.get("Accept") == "application/json"

    def test_json_headers_does_not_contain_output_format_as_key_variant(self):
        """Guard against typos like 'output_format' sneaking into the headers dict."""
        from presta.client import JSON_HEADERS
        assert "output_format" not in JSON_HEADERS