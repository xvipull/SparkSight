"""PySpark quality and enrichment transformations for SparkSight sales data."""
from __future__ import annotations

import logging

from pyspark.sql import DataFrame, functions as F

logger = logging.getLogger(__name__)

TEXT_COLUMNS = [
    "transaction_id", "customer_id", "customer_name", "customer_segment", "product_id", "product_name",
    "category", "sub_category", "region", "state", "city", "sales_channel", "payment_method", "order_status",
]
CATEGORY_MAP = {
    "electronics": "Electronics", "furniture": "Furniture", "office supplies": "Office Supplies",
    "clothing": "Clothing", "home appliances": "Home Appliances",
}
VALID_SEGMENTS = ["Consumer", "Corporate", "Small Business", "Enterprise"]
VALID_CHANNELS = ["Online", "Retail Store", "Marketplace", "Distributor"]
VALID_STATUSES = ["Completed", "Returned", "Cancelled"]


def _title_case(column: str):
    return F.initcap(F.lower(F.trim(F.col(column))))


def clean_and_enrich_sales(raw: DataFrame) -> DataFrame:
    """Clean raw transactions, validate financial values, and add analytical columns."""
    try:
        frame = raw.select(*raw.columns).dropDuplicates(["transaction_id"])
        for column in TEXT_COLUMNS:
            frame = frame.withColumn(column, F.when(F.trim(F.col(column)) == "", None).otherwise(F.trim(F.col(column))))

        frame = (frame
            .withColumn("order_date", F.to_date("order_date", "yyyy-MM-dd"))
            .withColumn("quantity", F.col("quantity").cast("int"))
            .withColumn("unit_price", F.col("unit_price").cast("double"))
            .withColumn("discount", F.coalesce(F.col("discount").cast("double"), F.lit(0.0)))
            .withColumn("revenue", F.col("revenue").cast("double"))
            .withColumn("cost", F.col("cost").cast("double"))
            .withColumn("customer_name", F.coalesce(F.col("customer_name"), F.lit("Unknown Customer")))
            .withColumn("city", F.coalesce(F.col("city"), F.lit("Unknown")))
            .withColumn("payment_method", F.coalesce(F.col("payment_method"), F.lit("Unknown")))
            .withColumn("category_key", F.lower(F.trim(F.col("category"))))
            .withColumn("category", F.coalesce(F.create_map(*sum(([F.lit(k), F.lit(v)] for k, v in CATEGORY_MAP.items()), [])).getItem(F.col("category_key")), F.initcap(F.col("category_key"))))
            .drop("category_key")
            .withColumn("customer_segment", _title_case("customer_segment"))
            .withColumn("region", _title_case("region"))
            .withColumn("state", _title_case("state"))
            .withColumn("city", _title_case("city"))
            .withColumn("sales_channel", _title_case("sales_channel"))
            .withColumn("payment_method", F.when(F.lower(F.col("payment_method")) == "upi", F.lit("UPI")).otherwise(_title_case("payment_method")))
            .withColumn("order_status", _title_case("order_status"))
        )
        # Reject incomplete, out-of-range, or unrecognized transactions before aggregates run.
        frame = frame.filter(
            F.col("transaction_id").isNotNull() & F.col("order_date").isNotNull() & F.col("customer_id").isNotNull()
            & F.col("product_id").isNotNull() & F.col("category").isNotNull() & F.col("region").isNotNull()
            & (F.col("quantity") > 0) & (F.col("unit_price") > 0) & F.col("discount").between(0, 0.75)
            & (F.col("cost") >= 0) & F.col("customer_segment").isin(VALID_SEGMENTS)
            & F.col("sales_channel").isin(VALID_CHANNELS) & F.col("order_status").isin(VALID_STATUSES)
        )
        expected_revenue = F.round(F.col("quantity") * F.col("unit_price") * (F.lit(1.0) - F.col("discount")), 2)
        frame = (frame
            .withColumn("revenue_is_valid", F.abs(F.col("revenue") - expected_revenue) <= F.lit(0.02))
            .withColumn("revenue", expected_revenue)  # canonical source after validation
            .withColumn("cost_is_valid", F.col("cost") <= F.col("revenue") * F.lit(1.25))
            .filter(F.col("cost_is_valid"))
            .withColumn("cost", F.round(F.col("cost"), 2))
            .withColumn("profit", F.round(F.col("revenue") - F.col("cost"), 2))
            .withColumn("discount_amount", F.round(F.col("quantity") * F.col("unit_price") * F.col("discount"), 2))
            .withColumn("profit_margin", F.round(F.when(F.col("revenue") != 0, F.col("profit") / F.col("revenue") * 100).otherwise(F.lit(0.0)), 2))
            .withColumn("year", F.year("order_date"))
            .withColumn("month", F.month("order_date"))
            .withColumn("year_month", F.date_format("order_date", "yyyy-MM"))
        )
        logger.info("Cleaned and enriched SparkSight sales data")
        return frame
    except Exception as exc:
        logger.exception("Sales transformations failed")
        raise RuntimeError("SparkSight could not transform sales data") from exc
