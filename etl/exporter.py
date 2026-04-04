import os
import pandas as pd
from presta.client import get_products, get_languages, get_product
from settings import MULTILANG_FIELDS, FLAT_FIELDS, COLUMN_ORDER


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
    languages = get_languages()
    lang_map = {int(lang["id"]): lang["iso_code"] for lang in languages}
    print("lang_map:", lang_map)

    products = get_products()
    print("products count:", len(products))
    print("first product raw:", products[0] if products else "empty")

    if not products:
        raise ValueError("No products returned from PrestaShop")

    rows = []
    for p in products:
        product = get_product(int(p["id"]))
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

    df = pd.DataFrame(rows)

    ordered_cols = [c for c in COLUMN_ORDER if c in df.columns]
    remaining = [c for c in df.columns if c not in ordered_cols]
    df = df[ordered_cols + remaining]

    os.makedirs("exports", exist_ok=True)
    path = "exports/products.csv"
    df.to_csv(path, index=False, encoding="utf-8-sig")
    return path
