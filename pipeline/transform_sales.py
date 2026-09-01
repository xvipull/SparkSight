"""Batch pipeline: validate raw sales CSV and publish Parquet for distributed reads."""
from pathlib import Path

from pyspark.sql import SparkSession, functions as F

ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "data" / "sales_transactions.csv"
OUTPUT = ROOT / "data" / "curated_sales"


def main() -> None:
    spark = SparkSession.builder.appName("SparkSight Sales Pipeline").master("local[*]").getOrCreate()
    sales = spark.read.option("header", True).option("inferSchema", True).csv(str(RAW))
    curated = (sales.withColumn("order_date", F.to_date("order_date"))
               .filter(F.col("order_id").isNotNull() & F.col("order_date").isNotNull())
               .withColumn("revenue", F.round(F.col("unit_price") * F.col("quantity") * (1 - F.col("discount")), 2))
               .withColumn("profit", F.round(F.col("revenue") - F.col("unit_cost") * F.col("quantity"), 2)))
    curated.write.mode("overwrite").partitionBy("region", "category").parquet(str(OUTPUT))
    print(f"SparkSight published {curated.count()} transactions to {OUTPUT}")
    spark.stop()


if __name__ == "__main__":
    main()
