import requests
from requests.auth import HTTPBasicAuth
from requests.exceptions import Timeout, ConnectionError, HTTPError
from xml.etree import ElementTree as ET
from nicegui import app
from settings import MULTILANG_FIELDS


# ─────────────────────────────────────────────
# Result type helpers
# Every public function returns one of these:
#   {"ok": True,  "value": data}
#   {"ok": False, "error": "human readable string"}
# ─────────────────────────────────────────────


def _ok(value):
    return {"ok": True, "value": value}


def _err(message: str):
    return {"ok": False, "error": message}


# ─────────────────────────────────────────────
# Internal: credentials
# ─────────────────────────────────────────────

# PS 8.1+ requires Output-Format as a header, not a query param
JSON_HEADERS = {
    "Accept": "application/json",
    "Output-Format": "JSON",
}


def _creds():
    """Returns (url, auth) or raises — internal only, always called inside guarded functions."""
    url = app.storage.user.get("presta_url", "").rstrip("/")
    key = app.storage.user.get("presta_api_key", "")
    if not url or not key:
        raise RuntimeError("PrestaShop credentials not configured. Go to /setup.")
    # Guard: ensure /api suffix is always present
    if not url.endswith("/api"):
        url = url + "/api"
    return url, HTTPBasicAuth(key, "")


# ─────────────────────────────────────────────
# Internal: raw HTTP helpers (still raise — consumed by guarded public functions)
# ─────────────────────────────────────────────


def _get(endpoint, params=None):
    if params is None:
        params = {}
    url, auth = _creds()
    response = requests.get(
        f"{url}/{endpoint}",
        auth=auth,
        headers=JSON_HEADERS,
        params={"display": "full", **params},
        timeout=10,
    )
    # DEBUG — remove after fix
    if response.status_code == 406:
        print(f"DEBUG 406 URL: {response.url}")
        print(f"DEBUG 406 Headers: {dict(response.headers)}")
        print(f"DEBUG 406 Body: {response.text[:500]}")
    response.raise_for_status()
    return response.json()


def _get_xml(endpoint):
    url, auth = _creds()
    response = requests.get(f"{url}/{endpoint}", auth=auth, timeout=10)
    response.raise_for_status()
    return response.text


def _patch(endpoint, xml_body: str):
    url, auth = _creds()
    response = requests.patch(
        f"{url}/{endpoint}",
        auth=auth,
        headers={"Content-Type": "text/xml"},
        data=xml_body.encode("utf-8"),
        timeout=10,
    )
    response.raise_for_status()
    return response.text


def _post(endpoint, xml_body: str):
    url, auth = _creds()
    response = requests.post(
        f"{url}/{endpoint}",
        auth=auth,
        headers={"Content-Type": "text/xml"},
        data=xml_body.encode("utf-8"),
        timeout=10,
    )
    response.raise_for_status()
    return response.text


# ─────────────────────────────────────────────
# Internal: exception → human readable error
# ─────────────────────────────────────────────


def _handle_exception(e: Exception) -> dict:
    if isinstance(e, Timeout):
        return _err(
            "PrestaShop took too long to respond (timeout). Check your connection."
        )
    if isinstance(e, ConnectionError):
        return _err("Could not reach PrestaShop. Check the URL in your setup.")
    if isinstance(e, HTTPError):
        status = e.response.status_code if e.response is not None else "unknown"
        if status == 401:
            return _err(
                "PrestaShop rejected the API key (401 Unauthorized). Check your setup."
            )
        if status == 403:
            return _err(
                "PrestaShop denied access (403 Forbidden). Check API key permissions."
            )
        if status == 404:
            return _err(
                "PrestaShop resource not found (404). Check the URL in your setup."
            )
        if status == 406:
            return _err(
                "PrestaShop refused the request format (406 Not Acceptable). "
                "Make sure your URL ends with /api and the webservice is enabled "
                "in Advanced Parameters → Webservice."
            )
        if status == 500:
            return _err(
                "PrestaShop returned a server error (500). The shop may be down."
            )
        return _err(f"PrestaShop returned an unexpected error (HTTP {status}).")
    if isinstance(e, RuntimeError):
        return _err(str(e))
    return _err(f"Unexpected error: {str(e)}")


# ─────────────────────────────────────────────
# Public: guarded API functions
# All return {"ok": True, "value": ...} or {"ok": False, "error": "..."}
# ─────────────────────────────────────────────


def get_languages() -> dict:
    try:
        data = _get("languages")
        languages = data.get("languages", [])
        if not languages:
            return _err(
                "No languages returned from PrestaShop. Check API key permissions."
            )
        return _ok(languages)
    except Exception as e:
        return _handle_exception(e)


def get_products() -> dict:
    try:
        data = _get("products", params={"limit": "0"})
        if isinstance(data, list):
            products = data
        else:
            products = data.get("products", [])
        if not products:
            return _err("No products found in PrestaShop. The catalog may be empty.")
        return _ok(products)
    except Exception as e:
        return _handle_exception(e)


def get_product(product_id: int) -> dict:
    try:
        data = _get(f"products/{product_id}")
        product = data.get("product", {})
        if not product:
            return _err(f"Product {product_id} not found in PrestaShop.")
        return _ok(product)
    except Exception as e:
        return _handle_exception(e)


def get_product_xml(product_id: int) -> dict:
    try:
        xml = _get_xml(f"products/{product_id}")
        return _ok(xml)
    except Exception as e:
        return _handle_exception(e)


def patch_product(product_id: int, fields: dict, lang_map: dict) -> dict:
    try:
        xml_body = _build_product_xml(product_id, fields, lang_map)
        result = _patch(f"products/{product_id}", xml_body)
        return _ok(result)
    except Exception as e:
        return _handle_exception(e)


def create_product(fields: dict, lang_map: dict) -> dict:
    try:
        xml_body = _build_product_xml(None, fields, lang_map)
        result = _post("products", xml_body)
        return _ok(result)
    except Exception as e:
        return _handle_exception(e)


# ─────────────────────────────────────────────
# Pure: XML builder — no guard needed, no side effects
# ─────────────────────────────────────────────


def _build_product_xml(product_id, fields: dict, lang_map: dict) -> str:
    MULTILANG_SET = set(MULTILANG_FIELDS)
    code_to_id = {v: k for k, v in lang_map.items()}

    root = ET.Element("prestashop")
    root.set("xmlns:xlink", "http://www.w3.org/1999/xlink")
    product_el = ET.SubElement(root, "product")

    if product_id:
        id_el = ET.SubElement(product_el, "id")
        id_el.text = str(product_id)

    multilang_groups = {}
    flat_fields = {}

    for col, value in fields.items():
        if value is None or str(value).strip() == "":
            continue

        matched = False
        for base in MULTILANG_SET:
            if col.startswith(f"{base}_"):
                lang_code = col[len(base) + 1:]
                if lang_code in code_to_id:
                    multilang_groups.setdefault(base, {})[lang_code] = str(value)
                    matched = True
                    break
        if not matched and col != "id":
            flat_fields[col] = str(value)

    for key, value in flat_fields.items():
        el = ET.SubElement(product_el, key)
        el.text = value

    for base, langs in multilang_groups.items():
        field_el = ET.SubElement(product_el, base)
        for lang_code, text in langs.items():
            lang_id = code_to_id[lang_code]
            lang_el = ET.SubElement(field_el, "language")
            lang_el.set("id", str(lang_id))
            lang_el.text = text

    return '<?xml version="1.0" encoding="UTF-8"?>' + ET.tostring(
        root, encoding="unicode"
    )