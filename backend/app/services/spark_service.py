from __future__ import annotations

from functools import lru_cache

from pyspark.sql import DataFrame, SparkSession, functions as F

from app.core.config import get_settings
from app.schemas import AnalyticsFilters, DashboardResponse, DimensionMetric, FilterOptions, Kpis, Transaction, TrendPoint


@lru_cache
def get_spark() -> SparkSession:
    settings = get_settings()
    return (
        SparkSession.builder.appName("SparkSight Analytics")
        .master(settings.spark_master)
        .config("spark.ui.enabled", "false")
        .config("spark.sql.session.timeZone", "UTC")
        .getOrCreate()
    )


class SalesAnalyticsService:
    """Executes Spark transformations powering every SparkSight dashboard value."""

    def _sales(self) -> DataFrame:
        path = get_settings().resolved_data_path
        if not path.exists():
            raise FileNotFoundError(f"SparkSight data file was not found: {path}")
        return (
            get_spark().read.option("header", True).option("inferSchema", True).csv(str(path))
            .withColumn("order_date", F.to_date("order_date"))
            .withColumn("revenue", F.round(F.col("unit_price") * F.col("quantity") * (1 - F.col("discount")), 2))
            .withColumn("profit", F.round(F.col("revenue") - (F.col("unit_cost") * F.col("quantity")), 2))
        )

    @staticmethod
    def _apply_filters(sales: DataFrame, filters: AnalyticsFilters) -> DataFrame:
        filtered = sales
        if filters.start_date:
            filtered = filtered.filter(F.col("order_date") >= F.lit(filters.start_date.isoformat()))
        if filters.end_date:
            filtered = filtered.filter(F.col("order_date") <= F.lit(filters.end_date.isoformat()))
        if filters.regions:
            filtered = filtered.filter(F.col("region").isin(filters.regions))
        if filters.categories:
            filtered = filtered.filter(F.col("category").isin(filters.categories))
        return filtered

    @staticmethod
    def _metrics(frame: DataFrame, dimension: str, limit: int | None = None) -> list[DimensionMetric]:
        result = frame.groupBy(dimension).agg(
            F.sum("revenue").alias("revenue"), F.sum("profit").alias("profit"), F.countDistinct("order_id").alias("orders")
        ).orderBy(F.desc("revenue"))
        if limit:
            result = result.limit(limit)
        return [DimensionMetric(name=row[dimension], revenue=round(row.revenue, 2), profit=round(row.profit, 2), orders=row.orders) for row in result.collect()]

    def filter_options(self) -> FilterOptions:
        sales = self._sales()
        bounds = sales.agg(F.min("order_date").alias("min_date"), F.max("order_date").alias("max_date")).first()
        return FilterOptions(
            regions=[row.region for row in sales.select("region").distinct().orderBy("region").collect()],
            categories=[row.category for row in sales.select("category").distinct().orderBy("category").collect()],
            min_date=bounds.min_date, max_date=bounds.max_date,
        )

    def dashboard(self, filters: AnalyticsFilters) -> DashboardResponse:
        sales = self._apply_filters(self._sales(), filters).cache()
        totals = sales.agg(
            F.coalesce(F.sum("revenue"), F.lit(0)).alias("revenue"), F.coalesce(F.sum("profit"), F.lit(0)).alias("profit"),
            F.countDistinct("order_id").alias("orders"), F.coalesce(F.sum("quantity"), F.lit(0)).alias("units_sold"),
        ).first()
        revenue, profit, orders = float(totals.revenue), float(totals.profit), int(totals.orders)
        trend = sales.withColumn("period", F.date_format("order_date", "MMM yyyy")).groupBy(
            "period", F.trunc("order_date", "month").alias("month_sort")
        ).agg(F.sum("revenue").alias("revenue"), F.sum("profit").alias("profit"), F.countDistinct("order_id").alias("orders")).orderBy("month_sort").collect()
        rows = sales.orderBy(F.desc("order_date"), F.desc("revenue")).limit(12).collect()
        response = DashboardResponse(
            filters=self.filter_options(),
            kpis=Kpis(revenue=round(revenue, 2), profit=round(profit, 2), orders=orders, units_sold=int(totals.units_sold), profit_margin=round(profit / revenue * 100 if revenue else 0, 1), average_order_value=round(revenue / orders if orders else 0, 2)),
            revenue_trend=[TrendPoint(period=r.period, revenue=round(r.revenue, 2), profit=round(r.profit, 2), orders=r.orders) for r in trend],
            category_performance=self._metrics(sales, "category"), regional_performance=self._metrics(sales, "region"), top_products=self._metrics(sales, "product", 6),
            transactions=[Transaction(order_id=r.order_id, order_date=r.order_date, region=r.region, category=r.category, product=r.product, customer=r.customer, quantity=r.quantity, revenue=round(r.revenue, 2), profit=round(r.profit, 2)) for r in rows],
        )
        sales.unpersist()
        return response
