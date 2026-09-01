"""Spark aggregation layer that returns JSON-serializable SparkSight analytics."""
from __future__ import annotations

import logging
import math
from datetime import date, datetime
from typing import Any

from pyspark.sql import DataFrame, Window, functions as F

from app.core.config import get_settings
from app.data_loader import load_sales_data
from app.schemas import ApiFilters
from app.transformations import apply_sales_filters, clean_and_enrich_sales

logger = logging.getLogger(__name__)


def _value(value: Any) -> Any:
    if isinstance(value, (date, datetime)):
        return value.isoformat()
    if isinstance(value, float):
        return round(value, 2) if math.isfinite(value) else 0.0
    return value


def _records(frame: DataFrame) -> list[dict[str, Any]]:
    return [{key: _value(value) for key, value in row.asDict(recursive=True).items()} for row in frame.collect()]


class SalesAnalytics:
    """Loads, caches, filters, and aggregates the distributed sales dataset."""

    def __init__(self) -> None:
        self._sales: DataFrame | None = None

    @property
    def sales(self) -> DataFrame:
        if self._sales is None:
            raw = load_sales_data(get_settings().resolved_data_path.parent / "sales.csv")
            self._sales = clean_and_enrich_sales(raw).cache()
            self._sales.count()  # materialize once; subsequent dashboard queries reuse the cache
            logger.info("Cached cleaned SparkSight sales DataFrame")
        return self._sales

    def filter_sales(self, filters: ApiFilters | None = None) -> DataFrame:
        return apply_sales_filters(self.sales, filters or ApiFilters())

    def get_filter_options(self) -> dict[str, Any]:
        bounds = self.sales.agg(F.min("order_date").alias("min_date"), F.max("order_date").alias("max_date")).first()
        return {
            "regions": [row.region for row in self.sales.select("region").distinct().orderBy("region").collect()],
            "categories": [row.category for row in self.sales.select("category").distinct().orderBy("category").collect()],
            "customer_segments": [row.customer_segment for row in self.sales.select("customer_segment").distinct().orderBy("customer_segment").collect()],
            "sales_channels": [row.sales_channel for row in self.sales.select("sales_channel").distinct().orderBy("sales_channel").collect()],
            "min_date": _value(bounds.min_date), "max_date": _value(bounds.max_date),
        }

    def get_overview_metrics(self, frame: DataFrame | None = None) -> dict[str, Any]:
        frame = frame if frame is not None else self.sales
        metrics = frame.agg(
            F.coalesce(F.sum("revenue"), F.lit(0.0)).alias("total_revenue"),
            F.coalesce(F.sum("profit"), F.lit(0.0)).alias("total_profit"),
            F.countDistinct("transaction_id").alias("total_orders"),
            F.coalesce(F.avg("revenue"), F.lit(0.0)).alias("average_order_value"),
            F.countDistinct("customer_id").alias("total_customers"), F.coalesce(F.sum("quantity"), F.lit(0)).alias("units_sold"),
            F.coalesce(F.avg(F.when(F.col("order_status") == "Returned", 1.0).otherwise(0.0)) * 100, F.lit(0.0)).alias("return_rate"),
        ).first().asDict()
        metrics["profit_margin"] = (metrics["total_profit"] / metrics["total_revenue"] * 100) if metrics["total_revenue"] else 0.0
        return {key: _value(value) for key, value in metrics.items()}

    def _performance(self, dimension: str, frame: DataFrame | None = None) -> list[dict[str, Any]]:
        frame = frame if frame is not None else self.sales
        return _records(frame.groupBy(dimension).agg(
            F.sum("revenue").alias("revenue"), F.sum("cost").alias("cost"), F.sum("profit").alias("profit"),
            F.countDistinct("transaction_id").alias("orders"), F.countDistinct("customer_id").alias("customers"), F.sum("quantity").alias("units_sold"),
            F.round(F.avg("profit_margin"), 2).alias("average_profit_margin"),
            F.round(F.sum("revenue") / F.countDistinct("transaction_id"), 2).alias("average_order_value"),
            F.round(F.sum("profit") / F.sum("revenue") * 100, 2).alias("profit_margin"),
        ).orderBy(F.desc("revenue")))

    def get_monthly_sales(self, frame: DataFrame | None = None) -> list[dict[str, Any]]:
        frame = frame if frame is not None else self.sales
        return _records(frame.groupBy("year", "month", "year_month").agg(F.sum("revenue").alias("revenue"), F.countDistinct("transaction_id").alias("orders"), F.sum("quantity").alias("units_sold")).orderBy("year", "month"))

    def get_monthly_profit(self, frame: DataFrame | None = None) -> list[dict[str, Any]]:
        frame = frame if frame is not None else self.sales
        return _records(frame.groupBy("year", "month", "year_month").agg(F.sum("profit").alias("profit"), F.round(F.avg("profit_margin"), 2).alias("average_profit_margin")).orderBy("year", "month"))

    def get_category_performance(self, frame: DataFrame | None = None) -> list[dict[str, Any]]:
        return self._performance("category", frame)

    def get_subcategory_performance(self, frame: DataFrame | None = None) -> list[dict[str, Any]]:
        return self._performance("sub_category", frame)

    def get_region_performance(self, frame: DataFrame | None = None) -> list[dict[str, Any]]:
        return self._performance("region", frame)

    def get_top_products(self, frame: DataFrame | None = None, limit: int = 10, sort_by: str = "revenue") -> list[dict[str, Any]]:
        frame = frame if frame is not None else self.sales
        products = frame.groupBy("product_id", "product_name", "category").agg(F.sum("revenue").alias("revenue"), F.sum("profit").alias("profit"), F.countDistinct("transaction_id").alias("orders"), F.sum("quantity").alias("units_sold"))
        metric = {"revenue": "revenue", "profit": "profit", "units_sold": "units_sold"}.get(sort_by, "revenue")
        ranked = products.withColumn("rank", F.row_number().over(Window.orderBy(F.desc(metric), F.asc("product_name")))).filter(F.col("rank") <= limit).orderBy("rank")
        return _records(ranked)

    def get_product_summary(self, frame: DataFrame | None = None) -> dict[str, Any]:
        frame = frame if frame is not None else self.sales
        totals = frame.agg(F.coalesce(F.sum("revenue"), F.lit(0.0)).alias("total_product_revenue"), F.coalesce(F.sum("profit"), F.lit(0.0)).alias("total_product_profit"), F.coalesce(F.sum("quantity"), F.lit(0)).alias("units_sold"), F.countDistinct("product_id").alias("number_products")).first().asDict()
        best = frame.groupBy("category").agg(F.sum("revenue").alias("revenue")).orderBy(F.desc("revenue")).first()
        totals["best_performing_category"] = best.category if best else "—"
        return {key: _value(value) for key, value in totals.items()}

    def get_top_customers(self, frame: DataFrame | None = None, limit: int = 10) -> list[dict[str, Any]]:
        frame = frame if frame is not None else self.sales
        customers = frame.groupBy("customer_id", "customer_name", "customer_segment").agg(F.sum("revenue").alias("revenue"), F.sum("profit").alias("profit"), F.countDistinct("transaction_id").alias("orders"))
        customers = customers.withColumn("average_order_value", F.round(F.col("revenue") / F.col("orders"), 2))
        return _records(customers.orderBy(F.desc("revenue")).limit(limit))

    def get_customer_summary(self, frame: DataFrame | None = None) -> dict[str, Any]:
        frame = frame if frame is not None else self.sales
        customer_orders = frame.groupBy("customer_id").agg(F.sum("revenue").alias("customer_revenue"), F.countDistinct("transaction_id").alias("customer_orders"))
        metrics = customer_orders.agg(
            F.count("customer_id").alias("total_customers"), F.coalesce(F.avg("customer_revenue"), F.lit(0.0)).alias("average_revenue_per_customer"),
            F.coalesce(F.avg(F.col("customer_revenue") / F.col("customer_orders")), F.lit(0.0)).alias("average_order_value"),
            F.coalesce(F.avg(F.when(F.col("customer_orders") > 1, 1.0).otherwise(0.0)) * 100, F.lit(0.0)).alias("returning_customer_rate"),
        ).first().asDict()
        return {key: _value(value) for key, value in metrics.items()}

    def get_customer_segments(self, frame: DataFrame | None = None) -> list[dict[str, Any]]:
        return self._performance("customer_segment", frame)

    def get_sales_channels(self, frame: DataFrame | None = None) -> list[dict[str, Any]]:
        return self._performance("sales_channel", frame)

    def get_payment_methods(self, frame: DataFrame | None = None) -> list[dict[str, Any]]:
        return self._performance("payment_method", frame)

    def get_order_status_distribution(self, frame: DataFrame | None = None) -> list[dict[str, Any]]:
        frame = frame if frame is not None else self.sales
        total = frame.count()
        return _records(frame.groupBy("order_status").agg(F.count("*").alias("transactions"), F.sum("revenue").alias("revenue"), F.sum("profit").alias("profit")).withColumn("percentage", F.round(F.col("transactions") / F.lit(total) * 100, 2)).orderBy(F.desc("transactions")))

    def get_discount_analysis(self, frame: DataFrame | None = None) -> list[dict[str, Any]]:
        frame = frame if frame is not None else self.sales
        bands = frame.withColumn("discount_band", F.when(F.col("discount") == 0, "No discount").when(F.col("discount") <= 0.05, "1-5%").when(F.col("discount") <= 0.10, "6-10%").when(F.col("discount") <= 0.15, "11-15%").otherwise("16%+"))
        return _records(bands.groupBy("discount_band").agg(F.count("*").alias("transactions"), F.avg("discount").alias("average_discount"), F.sum("discount_amount").alias("discount_amount"), F.sum("revenue").alias("revenue"), F.sum("profit").alias("profit")).orderBy(F.desc("discount_amount")))

    def get_profit_margin_analysis(self, frame: DataFrame | None = None) -> list[dict[str, Any]]:
        frame = frame if frame is not None else self.sales
        return _records(frame.groupBy("category").agg(F.round(F.avg("profit_margin"), 2).alias("average_profit_margin"), F.round(F.min("profit_margin"), 2).alias("minimum_profit_margin"), F.round(F.max("profit_margin"), 2).alias("maximum_profit_margin"), F.sum("profit").alias("profit")).orderBy(F.desc("average_profit_margin")))

    def get_recent_transactions(self, frame: DataFrame | None = None, limit: int = 12) -> list[dict[str, Any]]:
        frame = frame if frame is not None else self.sales
        return _records(frame.select("transaction_id", "order_date", "region", "category", "product_name", "customer_name", "quantity", "revenue", "profit").orderBy(F.desc("order_date"), F.desc("revenue")).limit(limit))
