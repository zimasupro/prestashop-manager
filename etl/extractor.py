import pandas as pd

from presta.client import (
    get_languages,
    get_order_details,
    get_orders,
    get_product,
    get_products,
)


def fetch_inventory() -> dict:
    lang_result = get_languages()
    if not lang_result["ok"]:
        return lang_result

    lang_map = {int(l["id"]): l["iso_code"] for l in lang_result["value"]}

    products_result = get_products()
    if not products_result["ok"]:
        return products_result

    rows = []
    for p in products_result["value"]:
        result = get_product(int(p["id"]))
        if not result["ok"]:
            continue
        prod = result["value"]

        name = prod.get("name", [])
        if isinstance(name, list):
            name = name[0].get("value", "") if name else ""
        elif isinstance(name, dict):
            name = name.get("language", [{}])
            name = name[0].get("value", "") if isinstance(name, list) and name else ""

        rows.append(
            {
                "id": int(prod["id"]),
                "reference": prod.get("reference", ""),
                "name": name,
                "price": float(prod.get("price", 0)),
                "wholesale_price": float(prod.get("wholesale_price", 0)),
                "quantity": 0,
                "sales_volume": 0,
            }
        )

    if not rows:
        return {"ok": False, "error": "No products could be fetched."}

    return {"ok": True, "value": pd.DataFrame(rows)}


def fetch_sales_history() -> dict:
    orders_result = get_orders()
    if not orders_result["ok"]:
        return orders_result

    order_date_map = {
        int(o["id"]): o["date_add"][:7]
        for o in orders_result["value"]
        if "id" in o and "date_add" in o
    }

    details_result = get_order_details()
    if not details_result["ok"]:
        return details_result

    sales = {}
    for od in details_result["value"]:
        try:
            product_id = int(od.get("product_id", 0))
            quantity = int(od.get("product_quantity", 0))
            order_id = int(od.get("id_order", 0))
        except (ValueError, TypeError):
            continue
        month = order_date_map.get(order_id, "unknown")
        key = (product_id, month)
        sales[key] = sales.get(key, 0) + quantity

    if not sales:
        return {
            "ok": False,
            "error": "No sales history found. Check order access permissions in PrestaShop → Webservice.",
        }

    rows = [
        {"product_id": pid, "month": month, "units_sold": qty}
        for (pid, month), qty in sorted(sales.items())
    ]

    return {"ok": True, "value": pd.DataFrame(rows)}
