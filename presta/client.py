from xml.etree import ElementTree as ET

import requests
from nicegui import app
from requests.auth import HTTPBasicAuth
from requests.exceptions import ConnectionError, HTTPError, Timeout

from settings import MULTILANG_FIELDS

# ─── result helpers ───────────────────────────────────────────────────────────
# Every public function returns one of these two shapes.
# {"ok": True,  "value": data}
# {"ok": False, "error": "human readable string"}
# Callers always check result["ok"] before using result["value"].


def _ok(value):
    return {"ok": True, "value": value}


def _err(message: str):
    return {"ok": False, "error": message}


# ─── credentials ──────────────────────────────────────────────────────────────
# Reads PrestaShop URL and API key from session storage.
# Raises RuntimeError if not configured — caught by _handle_exception.


def _creds():
    url = app.storage.user.get("presta_url", "").rstrip("/")
    key = app.storage.user.get("presta_api_key", "")
    http_user = app.storage.user.get("http_user", "").strip()
    http_pass = app.storage.user.get("http_pass", "").strip()

    if not url or not key:
        raise RuntimeError("PrestaShop credentials not configured. Go to /setup.")

    if http_user:
        auth = HTTPBasicAuth(http_user, http_pass)
        extra_params = {"ws_key": key}
    else:
        auth = HTTPBasicAuth(key, "")
        extra_params = {}

    return url, auth, extra_params


# ─── raw HTTP helpers ─────────────────────────────────────────────────────────
# These raise on failure. They are always called inside try/except in public functions.
# credentials param is optional — if provided bypasses storage (used by test_presta_connection).


def _get(endpoint, params=None, credentials=None):
    if params is None:
        params = {}
    if credentials is None:
        url, auth = _creds()
    else:
        url, auth = credentials
    response = requests.get(
        f"{url}/{endpoint}",
        auth=auth,
        params={"output_format": "JSON", "display": "full", **params},
        timeout=10,
    )
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


# ─── exception handler ────────────────────────────────────────────────────────
# Translates every possible HTTP and network failure into a human readable _err.
# Called in every public function's except block.


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
        if status == 500:
            return _err(
                "PrestaShop returned a server error (500). The shop may be down."
            )
        return _err(f"PrestaShop returned an unexpected error (HTTP {status}).")
    if isinstance(e, RuntimeError):
        return _err(str(e))
    return _err(f"Unexpected error: {str(e)}")


# ─── xml builder ──────────────────────────────────────────────────────────────
# PrestaShop requires XML for all write operations (POST and PATCH).
# This is complex because PrestaShop has two field types:
#   flat fields    — simple key/value. e.g. price, quantity, reference.
#   multilang fields — nested by language ID. e.g. name, description.
# Fields named like "name_en" or "description_de" are multilang.
# The lang_map argument maps language IDs to language codes e.g. {1: "en", 2: "de"}.


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
                lang_code = col[len(base) + 1 :]
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
        root,
        encoding="unicode",
    )


# ─── public API ───────────────────────────────────────────────────────────────
# All public functions return {"ok": True, "value": ...} or {"ok": False, "error": "..."}.
# Callers never see raw exceptions. Everything is caught and translated here.


def test_presta_connection(url: str, api_key: str) -> dict:
    try:
        credentials = (url, HTTPBasicAuth(api_key, ""))
        data = _get("languages", credentials=credentials)
        languages = data.get("languages", [])
        if not languages:
            return _err("Connected but no languages found. Check API key permissions.")
        return _ok(languages)
    except Exception as e:
        return _handle_exception(e)


def save_presta_credentials(url: str, api_key: str) -> None:
    app.storage.user["presta_url"] = url.rstrip("/")
    app.storage.user["presta_api_key"] = api_key


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
    # PrestaShop returns a bare list for products instead of a wrapped object.
    # This is inconsistent with every other endpoint which returns {"resource": [...]}
    # We handle both shapes here.
    try:
        url, auth = _creds()
        response = requests.get(
            f"{url}/products",
            auth=auth,
            params={"output_format": "JSON"},
            timeout=10,
        )
        response.raise_for_status()
        data = response.json()
        products = data if isinstance(data, list) else data.get("products", [])
        if not products:
            return _err("No products found in PrestaShop. The catalog may be empty.")
        return _ok(products)
    except Exception as e:
        return _handle_exception(e)


def get_product(product_id: int) -> dict:
    try:
        url, auth = _creds()
        response = requests.get(
            f"{url}/products/{product_id}",
            auth=auth,
            params={"output_format": "JSON"},
            timeout=10,
        )
        response.raise_for_status()
        product = response.json().get("product", {})
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


def get_orders() -> dict:
    try:
        data = _get("orders", params={"limit": "0"})
        orders = data.get("orders", [])
        return _ok(orders)
    except Exception as e:
        return _handle_exception(e)


def get_order_details() -> dict:
    try:
        data = _get("order_details", params={"limit": "0"})
        details = data.get("order_details", [])
        return _ok(details)
    except Exception as e:
        return _handle_exception(e)


def get_orders() -> dict:
    try:
        data = _get("orders", params={"limit": "0"})
        orders = data.get("orders", [])
        if not orders:
            return _err("No orders found. The store may have no order history.")
        return _ok(orders)
    except Exception as e:
        return _handle_exception(e)


def get_order_details() -> dict:
    try:
        data = _get("order_details", params={"limit": "0"})
        details = data.get("order_details", [])
        if not details:
            return _err("No order details found.")
        return _ok(details)
    except Exception as e:
        return _handle_exception(e)
