import os
import pandas as pd
from presta.client import get_products, get_languages, get_product
from settings import MULTILANG_FIELDS, FLAT_FIELDS, COLUMN_ORDER
import tempfile
import uuid


def flatten_multilang(value, lang_map):
    if not value:
        return {}

    # Case: plain string
    if isinstance(value, str):
        default_lang = lang_map.get(1)
        if default_lang:
            return {default_lang: value}
        if lang_map:
            return {next(iter(lang_map.values())): value}
        return {}

    # Case: wrapped in {"language": ...}
    if isinstance(value, dict):
        value = value.get("language", [])
        # single language → dict not list, normalize
        if isinstance(value, dict):
            value = [value]

    if not isinstance(value, list):
        return {}

    result = {}
    for item in value:
        if not isinstance(item, dict):
            continue
        raw_id = item.get("id")
        text = item.get("value", "")
        if raw_id is None:
            continue
        try:
            lang_code = lang_map.get(int(raw_id))
        except (ValueError, TypeError):
            continue
        if lang_code:
            result[lang_code] = text

    return result


def export_products_csv(fields=None):

    # --- GUARDED: fetch languages ---
    lang_result = get_languages()
    if not lang_result["ok"]:
        raise RuntimeError(f"Could not fetch languages: {lang_result['error']}")
    lang_map = {int(lang["id"]): lang["iso_code"] for lang in lang_result["value"]}

    print("lang_map:", lang_map)

    # --- GUARDED: fetch products ---
    products_result = get_products()
    if not products_result["ok"]:
        raise RuntimeError(f"Could not fetch products: {products_result['error']}")
    products = products_result["value"]

    print("products count:", len(products))
    print("first product raw:", products[0] if products else "empty")

    rows = []
    for p in products:

        # --- GUARDED: fetch individual product ---
        product_result = get_product(int(p["id"]))
        if not product_result["ok"]:
            print(f"Skipping product {p['id']}: {product_result['error']}")
            continue
        product = product_result["value"]

        print("fetched product id:", p["id"], "keys:", list(product.keys())[:5])
        row = {}
        for key, value in product.items():
            if key in MULTILANG_FIELDS:
                flattened = flatten_multilang(value, lang_map)
                for lang_code, text in flattened.items():
                    col = f"{key}_{lang_code}"
                    if fields is None or col in fields:
                        row[col] = text
            else:
                if fields is None or key in fields:
                    row[key] = value
        rows.append(row)

    if not rows:
        raise RuntimeError(
            "No products could be exported. All products failed to fetch."
        )

    df = pd.DataFrame(rows)

    ordered_cols = [c for c in COLUMN_ORDER if c in df.columns]
    remaining = [c for c in df.columns if c not in ordered_cols]
    df = df[ordered_cols + remaining]

    os.makedirs("/tmp/exports", exist_ok=True)
    filename = f"products_{uuid.uuid4().hex}.csv"
    path = os.path.join(tempfile.gettempdir(), "exports", filename)
    df.to_csv(path, index=False, encoding="utf-8-sig")

    # --- GUARDED: verify file actually written ---
    if not os.path.exists(path):
        raise RuntimeError("Export file could not be written to disk.")

    return path
