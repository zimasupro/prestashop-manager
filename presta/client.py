import requests
from requests.auth import HTTPBasicAuth
from xml.etree import ElementTree as ET
from nicegui import app
from settings import MULTILANG_FIELDS


def _creds():
    url = app.storage.user.get("presta_url", "").rstrip("/")
    key = app.storage.user.get("presta_api_key", "")
    if not url or not key:
        raise RuntimeError("PrestaShop credentials not configured. Go to /setup.")
    return url, HTTPBasicAuth(key, "")


def _get(endpoint, params=None):
    if params is None:
        params = {}
    url, auth = _creds()
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


def get_languages():
    data = _get("languages")
    return data.get("languages", [])


def get_products():
    url, auth = _creds()
    response = requests.get(
        f"{url}/products", auth=auth, params={"output_format": "JSON"}, timeout=10
    )
    response.raise_for_status()
    return response.json().get("products", [])


def get_product(product_id: int):
    data = _get(f"products/{product_id}")
    return data.get("product", {})


def get_product_xml(product_id: int):
    return _get_xml(f"products/{product_id}")


def patch_product(product_id: int, fields: dict, lang_map: dict):
    xml_body = _build_product_xml(product_id, fields, lang_map)
    return _patch(f"products/{product_id}", xml_body)


def create_product(fields: dict, lang_map: dict):
    xml_body = _build_product_xml(None, fields, lang_map)
    return _post("products", xml_body)


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
        root, encoding="unicode"
    )
