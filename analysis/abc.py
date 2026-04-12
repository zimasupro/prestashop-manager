import pandas as pd


def calculate_abc(
    df: pd.DataFrame,
    threshold_a: float = 0.70,
    threshold_b: float = 0.90,
) -> pd.DataFrame:
    df = df.copy()
    df["revenue"] = (df["price"] * df["sales_volume"]).round(2)
    df = df.sort_values("revenue", ascending=False).reset_index(drop=True)

    total = df["revenue"].sum()
    df["revenue_pct"] = (df["revenue"] / total * 100).round(2)
    df["cumulative_revenue"] = df["revenue"].cumsum().round(2)
    df["cumulative_revenue_pct"] = (df["cumulative_revenue"] / total * 100).round(2)

    df["abc_class"] = pd.cut(
        df["cumulative_revenue_pct"],
        bins=[0, threshold_a * 100, threshold_b * 100, 100],
        labels=["A", "B", "C"],
        include_lowest=True,
    )

    return df
