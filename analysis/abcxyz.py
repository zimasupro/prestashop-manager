import pandas as pd

from analysis.abc import calculate_abc
from analysis.xyz import calculate_xyz
from settings import ABCXYZ_INTERPRETATIONS


def calculate_abcxyz(
    inventory_df: pd.DataFrame,
    sales_df: pd.DataFrame,
    threshold_a: float = 0.70,
    threshold_b: float = 0.90,
    threshold_x: float = 0.30,
    threshold_y: float = 0.60,
) -> pd.DataFrame:
    abc = calculate_abc(inventory_df, threshold_a, threshold_b)
    xyz = calculate_xyz(sales_df, threshold_x, threshold_y)

    df = abc.merge(
        xyz[["product_id", "sales_mean", "sales_std", "cv", "xyz_class"]],
        left_on="id",
        right_on="product_id",
        how="left",
    ).drop(columns="product_id")

    if "Z" not in df["xyz_class"].cat.categories:
        df["xyz_class"] = df["xyz_class"].cat.add_categories("Z")
    df["xyz_class"] = df["xyz_class"].fillna("Z")

    df["abcxyz_class"] = df["abc_class"].astype(str) + df["xyz_class"].astype(str)
    df["interpretation"] = df["abcxyz_class"].map(ABCXYZ_INTERPRETATIONS)

    return df
