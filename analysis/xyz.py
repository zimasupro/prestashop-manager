import numpy as np
import pandas as pd


def calculate_xyz(
    df: pd.DataFrame,
    threshold_x: float = 0.30,
    threshold_y: float = 0.60,
) -> pd.DataFrame:
    stats = (
        df.groupby("product_id")["units_sold"]
        .agg(sales_mean="mean", sales_std="std")
        .reset_index()
    )

    stats["sales_mean"] = stats["sales_mean"].round(2)
    stats["sales_std"] = stats["sales_std"].fillna(0).round(2)
    stats["cv"] = (
        (stats["sales_std"] / stats["sales_mean"].replace(0, np.nan))
        .round(4)
        .fillna(np.inf)
    )

    stats["xyz_class"] = pd.cut(
        stats["cv"],
        bins=[0, threshold_x, threshold_y, np.inf],
        labels=["X", "Y", "Z"],
        include_lowest=True,
    )

    return stats
