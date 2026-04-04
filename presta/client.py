import requests
from requests.auth import HTTPBasicAuth
from xml.etree import ElementTree as ET
from config import PRESTA_URL, PRESTA_API_KEY
from settings import MULTILANG_FIELDS


def _auth():
    return HTTPBasicAuth(PRESTA_API_KEY, "")


def _get(endpoint, params=None):
    if params is None:
        params = {}
    response = requests.get(
        f"{PRESTA_URL}/{endpoint}",
        auth=_auth(),
        params={"output_format": "JSON", "display": "full", **params},
    )
    response.raise_for_status()
    return response.json()


def _get_xml(endpoint):
    """Fetch a single resource as raw XML — used before PUT/PATCH."""
    response = requests.get(
        f"{PRESTA_URL}/{endpoint}",
        auth=_auth(),
    )
    response.raise_for_status()
    return response.text


def _patch(endpoint, xml_body: str):
    """Partial update — only sends fields included in xml_body."""
    response = requests.patch(
        f"{PRESTA_URL}/{endpoint}",
        auth=_auth(),
        headers={"Content-Type": "text/xml"},
        data=xml_body.encode("utf-8"),
    )
    response.raise_for_status()
    return response.text


def _post(endpoint, xml_body: str):
    """Create a new resource."""
    response = requests.post(
        f"{PRESTA_URL}/{endpoint}",
        auth=_auth(),
        headers={"Content-Type": "text/xml"},
        data=xml_body.encode("utf-8"),
    )
    response.raise_for_status()
    return response.text


def get_languages():
    data = _get("languages")
    return data.get("languages", [])


def get_products():
    """Get product IDs only — fetch individual products via get_product()."""
    response = requests.get(
        f"{PRESTA_URL}/products",
        auth=_auth(),
        params={"output_format": "JSON"},
    )
    response.raise_for_status()
    return response.json().get("products", [])


def get_product(product_id: int):
    data = _get(f"products/{product_id}")
    products = data.get("products", [])
    return products[0] if products else {}


def get_product_xml(product_id: int):
    """Get a single product as raw XML — needed for full PUT."""
    return _get_xml(f"products/{product_id}")


def patch_product(product_id: int, fields: dict, lang_map: dict):
    """
    Partial update a product.
    fields = {"name_en": "Blue Shirt", "price": "29.99"}
    lang_map = {1: "en", 2: "de", 3: "id"}
    """
    xml_body = _build_product_xml(product_id, fields, lang_map)
    return _patch(f"products/{product_id}", xml_body)


def create_product(fields: dict, lang_map: dict):
    """Create a new product."""
    xml_body = _build_product_xml(None, fields, lang_map)
    return _post("products", xml_body)


def _build_product_xml(product_id, fields: dict, lang_map: dict) -> str:
    """
    Build minimal XML for PATCH or POST.
    Only includes fields that are present and non-empty.

    lang_map = {1: "en", 2: "de", 3: "id"}
    fields = {"name_en": "Blue Shirt", "price": "29.99"}
    """
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
