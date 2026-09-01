"""Compatibility adapter from Spark engineering analytics to dashboard response models."""
from __future__ import annotations

from app.analytics import SalesAnalytics
from app.schemas import AnalyticsFilters, ApiFilters, DashboardResponse, DimensionMetric, FilterOptions, Kpis, Transaction, TrendPoint


class SalesAnalyticsService:
    def __init__(self) -> None:
        self.analytics = SalesAnalytics()

    def filter_options(self) -> FilterOptions:
        return FilterOptions(**self.analytics.get_filter_options())

    @staticmethod
    def _dimensions(rows: list[dict], name_field: str) -> list[DimensionMetric]:
        return [DimensionMetric(name=row[name_field], revenue=row["revenue"], profit=row["profit"], orders=row["orders"]) for row in rows]

    def dashboard(self, filters: AnalyticsFilters) -> DashboardResponse:
        frame = self.analytics.filter_sales(ApiFilters(start_date=filters.start_date, end_date=filters.end_date, region=filters.regions[0] if filters.regions else None, category=filters.categories[0] if filters.categories else None, customer_segment=filters.customer_segments[0] if filters.customer_segments else None, sales_channel=filters.sales_channels[0] if filters.sales_channels else None))
        overview = self.analytics.get_overview_metrics(frame)
        monthly_sales = {row["year_month"]: row for row in self.analytics.get_monthly_sales(frame)}
        monthly_profit = {row["year_month"]: row for row in self.analytics.get_monthly_profit(frame)}
        trend = [TrendPoint(period=period, revenue=row["revenue"], profit=monthly_profit[period]["profit"], orders=row["orders"]) for period, row in monthly_sales.items()]
        recent = self.analytics.get_recent_transactions(frame)
        return DashboardResponse(
            filters=self.filter_options(),
            kpis=Kpis(revenue=overview["total_revenue"], profit=overview["total_profit"], orders=overview["total_orders"], units_sold=overview["units_sold"], profit_margin=overview["profit_margin"], average_order_value=overview["average_order_value"]),
            revenue_trend=trend,
            category_performance=self._dimensions(self.analytics.get_category_performance(frame), "category"),
            regional_performance=self._dimensions(self.analytics.get_region_performance(frame), "region"),
            top_products=self._dimensions(self.analytics.get_top_products(frame, 6), "product_name"),
            transactions=[Transaction(order_id=row["transaction_id"], order_date=row["order_date"], region=row["region"], category=row["category"], product=row["product_name"], customer=row["customer_name"], quantity=row["quantity"], revenue=row["revenue"], profit=row["profit"]) for row in recent],
        )
