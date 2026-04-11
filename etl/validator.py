from bs4 import BeautifulSoup
import pandas as pd
import re
from settings import DESCRIPTION_FIELDS, REQUIRED_FIELDS, ALLOWED_TAGS


def clean_html(raw_html: str) -> tuple[str, list[str]]:
    """Clean a single HTML string. Returns (clean_html, list_of_changes)."""
    if not raw_html or not isinstance(raw_html, str):
        return raw_html, []

    changes = []
    soup = BeautifulSoup(raw_html, "html.parser")

    for tag in soup.find_all(True):
        if tag.name not in ALLOWED_TAGS:
            tag.unwrap()
            changes.append(f"removed <{tag.name}>")
            continue

        if tag.get("style"):
            del tag["style"]
            changes.append(f"removed inline style from <{tag.name}>")

        if tag.get("class"):
            del tag["class"]
            changes.append(f"removed class from <{tag.name}>")

        if tag.name == "h1":
            tag.name = "h2"
            changes.append("normalized h1 → h2")

    cleaned = str(soup)
    if "&nbsp;" in cleaned or "\xa0" in cleaned:
        cleaned = cleaned.replace("&nbsp;", " ").replace("\xa0", " ")
        changes.append("replaced &nbsp; with spaces")

    cleaned = re.sub(r" {2,}", " ", cleaned)

    return cleaned.strip(), list(set(changes))


def validate(df: pd.DataFrame) -> tuple[dict, pd.DataFrame]:
    """
    Validate and clean a product DataFrame.
    Returns (report, clean_df)

    report = {
        "fatal": [...],       # blocks import
        "warnings": [...],    # shown but import allowed
        "cleaned": [...],     # auto-fixed, logged
        "ok": True/False
    }
    """
    report = {
        "fatal": [],
        "warnings": [],
        "cleaned": [],
        "ok": True,
    }

    df = df.copy()

    # --- FATAL: required columns ---
    for field in REQUIRED_FIELDS:
        if field not in df.columns:
            report["fatal"].append(f"Missing required column: '{field}'")

    # --- FATAL: at least one name_xx column must exist ---
    name_cols = [c for c in df.columns if c.startswith("name_")]
    if not name_cols:
        report["fatal"].append("No name columns found (expected name_en, name_de etc.)")

    if report["fatal"]:
        report["ok"] = False
        return report, df

    # --- ROW LEVEL CHECKS ---
    for idx, row in df.iterrows():
        row_id = row.get("id", f"row {idx}")

        # FATAL: empty id
        if pd.isna(row.get("id")) or str(row.get("id", "")).strip() == "":
            report["fatal"].append(f"Row {idx}: empty id")
            report["ok"] = False

        # FATAL: all name fields empty
        name_values = [row.get(c) for c in name_cols]
        if all(pd.isna(v) or str(v).strip() == "" for v in name_values):
            report["fatal"].append(f"Product {row_id}: all name fields are empty")
            report["ok"] = False

        # WARNING: price is 0 or negative
        if "price" in df.columns:
            try:
                price = float(row.get("price", 1))
                if price <= 0:
                    report["warnings"].append(f"Product {row_id}: price is {price}")
            except (ValueError, TypeError):
                report["warnings"].append(f"Product {row_id}: price is not a number")

        # WARNING: active is not 0 or 1
        if "active" in df.columns:
            active = str(row.get("active", "")).strip()
            if active not in ("0", "1", ""):
                report["warnings"].append(
                    f"Product {row_id}: active='{active}' (expected 0 or 1)"
                )

        # AUTO-CLEAN: HTML description fields
        for base_field in DESCRIPTION_FIELDS:
            for col in df.columns:
                if col.startswith(f"{base_field}_"):
                    raw = row.get(col)
                    if pd.isna(raw) or not str(raw).strip():
                        continue
                    cleaned, changes = clean_html(str(raw))
                    if changes:
                        df.at[idx, col] = cleaned
                        for change in changes:
                            report["cleaned"].append(
                                f"Product {row_id} [{col}]: {change}"
                            )

    return report, df
