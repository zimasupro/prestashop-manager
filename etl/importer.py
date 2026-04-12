import pandas as pd

from presta.client import create_product, get_languages, get_product, patch_product
from settings import REQUIRED_CREATE_FIELDS


def _build_lang_map(languages):
    """Returns both directions:
    int_map = {1: "en", 2: "de", 3: "id"}
    """
    return {int(lang["id"]): lang["iso_code"] for lang in languages}


def _row_to_fields(row: dict) -> dict:
    """
    Convert a CSV row dict to a fields dict.
    Skips empty/null values — golden rule.
    """
    return {
        k: v
        for k, v in row.items()
        if v is not None and str(v).strip() != "" and str(v).strip().lower() != "nan"
    }


def import_products_csv(df: pd.DataFrame, dry_run: bool = True) -> dict:
    """
    Import products from a validated DataFrame.

    dry_run=True  → compute what would happen, don't push anything
    dry_run=False → actually push to PrestaShop

    Returns a report dict.
    """

    # --- GUARDED: fetch languages ---
    lang_result = get_languages()
    if not lang_result["ok"]:
        return {
            "dry_run": dry_run,
            "to_update": [],
            "to_create": [],
            "skipped": [],
            "errors": [f"Could not fetch languages: {lang_result['error']}"],
        }

    lang_map = _build_lang_map(lang_result["value"])

    report = {
        "dry_run": dry_run,
        "to_update": [],
        "to_create": [],
        "skipped": [],
        "errors": [],
    }

    for idx, row in df.iterrows():
        row_dict = row.to_dict()
        fields = _row_to_fields(row_dict)

        product_id = fields.get("id")

        # --- DETERMINE OPERATION ---
        if not product_id or str(product_id).strip() == "":
            operation = "create"
            product_id = None
        else:
            try:
                product_id = int(float(str(product_id)))
                operation = "update"
            except (ValueError, TypeError):
                report["skipped"].append(
                    f"Row {idx}: invalid id '{product_id}' — skipped"
                )
                continue

        # --- VALIDATE MINIMUM FIELDS FOR CREATE ---
        if operation == "create":
            missing = []
            for required in REQUIRED_CREATE_FIELDS:
                has_field = any(k.startswith(f"{required}_") for k in fields)
                if not has_field:
                    missing.append(required)
            if missing:
                report["skipped"].append(
                    f"Row {idx}: cannot create — missing required fields: {missing}"
                )
                continue
            report["to_create"].append(fields)
        else:
            report["to_update"].append({"id": product_id, "fields": fields})

        # --- DRY RUN STOPS HERE ---
        if dry_run:
            continue

        # --- ACTUAL PUSH — guarded ---
        if operation == "update":
            result = patch_product(product_id, fields, lang_map)
            if not result["ok"]:
                report["errors"].append(f"Product {product_id}: {result['error']}")
        else:
            result = create_product(fields, lang_map)
            if not result["ok"]:
                report["errors"].append(f"Row {idx}: {result['error']}")

    return report
