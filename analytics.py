"""Reusable analytics functions for Commerce Analytics Studio."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable

import pandas as pd


REQUIRED_COLUMNS = {
    "order_date",
    "order_id",
    "customer",
    "country",
    "product",
    "category",
    "quantity",
    "unit_price",
    "stock",
}


@dataclass(frozen=True)
class Metrics:
    revenue: float
    orders: int
    units: int
    average_order_value: float


def missing_columns(columns: Iterable[str]) -> set[str]:
    """Return required fields that are absent from a dataset."""
    return REQUIRED_COLUMNS.difference(columns)


def prepare_data(frame: pd.DataFrame) -> pd.DataFrame:
    """Validate, normalize and enrich uploaded commerce data."""
    data = frame.copy()
    data.columns = [str(column).strip().lower() for column in data.columns]

    missing = missing_columns(data.columns)
    if missing:
        raise ValueError(f"Missing required columns: {', '.join(sorted(missing))}")

    data["order_date"] = pd.to_datetime(data["order_date"], errors="coerce")
    for column in ("quantity", "unit_price", "stock"):
        data[column] = pd.to_numeric(data[column], errors="coerce")

    data = data.dropna(
        subset=["order_date", "order_id", "product", "quantity", "unit_price"]
    )
    data = data[(data["quantity"] > 0) & (data["unit_price"] >= 0)]
    data["revenue"] = data["quantity"] * data["unit_price"]
    data["month"] = data["order_date"].dt.to_period("M").astype(str)
    return data.sort_values("order_date")


def calculate_metrics(data: pd.DataFrame) -> Metrics:
    """Calculate top-level business metrics."""
    orders = int(data["order_id"].nunique())
    revenue = float(data["revenue"].sum())
    return Metrics(
        revenue=revenue,
        orders=orders,
        units=int(data["quantity"].sum()),
        average_order_value=revenue / orders if orders else 0.0,
    )


def revenue_by_month(data: pd.DataFrame) -> pd.DataFrame:
    return data.groupby("month", as_index=False)["revenue"].sum()


def product_performance(data: pd.DataFrame) -> pd.DataFrame:
    return (
        data.groupby(["product", "category"], as_index=False)
        .agg(revenue=("revenue", "sum"), units=("quantity", "sum"), stock=("stock", "min"))
        .sort_values("revenue", ascending=False)
    )


def dimension_revenue(data: pd.DataFrame, dimension: str) -> pd.DataFrame:
    if dimension not in {"country", "customer", "category"}:
        raise ValueError("Unsupported analysis dimension")
    return (
        data.groupby(dimension, as_index=False)["revenue"]
        .sum()
        .sort_values("revenue", ascending=False)
    )


def low_stock_products(data: pd.DataFrame, threshold: int = 15) -> pd.DataFrame:
    stock = data.groupby("product", as_index=False)["stock"].min()
    return stock[stock["stock"] <= threshold].sort_values("stock")
