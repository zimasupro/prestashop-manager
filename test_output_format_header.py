"""
test_output_format_header.py — Verifies PS 8.1+ Output-Format header behaviour
PrestaShop 8.1+ requires `Output-Format: JSON` as a request header.
Sending `output_format=JSON` as a query param causes a 406.

Run with: pytest test_output_format_header.py -v
"""

import pytest
from unittest.mock import patch, MagicMock

# NOTE: _creds() now returns 3 values: (url, auth, extra_params)
MOCK_CREDS = ("https://shop.example.com/api", MagicMock(), {})


def mock_json_response(data):
    mock = MagicMock()
    mock.json.return_value = data
    mock.raise_for_status = MagicMock()
    return mock


class TestOutputFormatHeader:

    @patch("presta.client._creds", return_value=MOCK_CREDS)
    @patch("requests.get")
    def test_get_languages_sends_output_format_header(self, mock_get, mock_creds):
        from presta.client import get_languages
        mock_get.return_value = mock_json_response({"languages": [{"id": "1", "iso_code": "en"}]})
        get_languages()
        assert mock_get.call_args[1]["headers"].get("Output-Format") == "JSON"

    @patch("presta.client._creds", return_value=MOCK_CREDS)
    @patch("requests.get")
    def test_get_languages_does_not_send_output_format_as_param(self, mock_get, mock_creds):
        from presta.client import get_languages
        mock_get.return_value = mock_json_response({"languages": [{"id": "1", "iso_code": "en"}]})
        get_languages()
        assert "output_format" not in mock_get.call_args[1]["params"]

    @patch("presta.client._creds", return_value=MOCK_CREDS)
    @patch("requests.get")
    def test_get_products_sends_output_format_header(self, mock_get, mock_creds):
        from presta.client import get_products
        mock_get.return_value = mock_json_response({"products": [{"id": "1"}]})
        get_products()
        assert mock_get.call_args[1]["headers"].get("Output-Format") == "JSON"

    @patch("presta.client._creds", return_value=MOCK_CREDS)
    @patch("requests.get")
    def test_get_product_sends_output_format_header(self, mock_get, mock_creds):
        from presta.client import get_product
        mock_get.return_value = mock_json_response({"product": {"id": "1"}})
        get_product(1)
        assert mock_get.call_args[1]["headers"].get("Output-Format") == "JSON"

    @patch("presta.client._creds", return_value=MOCK_CREDS)
    @patch("requests.get")
    def test_accept_and_output_format_both_present(self, mock_get, mock_creds):
        from presta.client import get_languages
        mock_get.return_value = mock_json_response({"languages": [{"id": "1", "iso_code": "en"}]})
        get_languages()
        headers = mock_get.call_args[1]["headers"]
        assert headers.get("Accept") == "application/json"
        assert headers.get("Output-Format") == "JSON"


class TestJsonHeadersConstant:

    def test_json_headers_contains_output_format(self):
        from presta.client import JSON_HEADERS
        assert JSON_HEADERS.get("Output-Format") == "JSON"

    def test_json_headers_contains_accept(self):
        from presta.client import JSON_HEADERS
        assert JSON_HEADERS.get("Accept") == "application/json"

    def test_no_output_format_as_query_key(self):
        from presta.client import JSON_HEADERS
        assert "output_format" not in JSON_HEADERS