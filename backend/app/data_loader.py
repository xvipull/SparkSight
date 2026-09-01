"""Schema-first loading for SparkSight raw sales data."""
from __future__ import annotations

import logging
from pathlib import Path

from pyspark.sql import DataFrame
from pyspark.sql.types import DoubleType, IntegerType, StringType, StructField, StructType

from app.spark_session import get_spark_session

logger = logging.getLogger(__name__)

SALES_SCHEMA = StructType([
    StructField("transaction_id", StringType(), True), StructField("order_date", StringType(), True),
    StructField("customer_id", StringType(), True), StructField("customer_name", StringType(), True),
    StructField("customer_segment", StringType(), True), StructField("product_id", StringType(), True),
    StructField("product_name", StringType(), True), StructField("category", StringType(), True),
    StructField("sub_category", StringType(), True), StructField("region", StringType(), True),
    StructField("state", StringType(), True), StructField("city", StringType(), True),
    StructField("sales_channel", StringType(), True), StructField("quantity", IntegerType(), True),
    StructField("unit_price", DoubleType(), True), StructField("discount", DoubleType(), True),
    StructField("revenue", DoubleType(), True), StructField("cost", DoubleType(), True),
    StructField("profit", DoubleType(), True), StructField("payment_method", StringType(), True),
    StructField("order_status", StringType(), True),
])


def load_sales_data(data_path: Path) -> DataFrame:
    """Read the raw CSV with explicit types; malformed values become null for cleaning."""
    if not data_path.exists():
        raise FileNotFoundError(f"SparkSight source data was not found: {data_path}")
    try:
        frame = (
            get_spark_session().read.option("header", True).option("mode", "PERMISSIVE")
            .option("nullValue", "").schema(SALES_SCHEMA).csv(str(data_path))
        )
        logger.info("Loaded SparkSight raw data from %s", data_path)
        return frame
    except Exception as exc:
        logger.exception("Unable to load sales CSV")
        raise RuntimeError("SparkSight could not load the sales dataset") from exc
