from __future__ import annotations

from datetime import date
from typing import Any, Optional

from pydantic import BaseModel, ConfigDict, Field


class HealthResponse(BaseModel):
    status: str
    service: str
    analytics_engine: str


class PipelineStatusResponse(BaseModel):
    status: str
    records_processed: int
    data_source: str
    processing_engine: str
    api: str
    frontend: str


class OverviewResponse(BaseModel):
    model_config = ConfigDict(populate_by_name=True)
    total_revenue: float = Field(serialization_alias="totalRevenue")
    total_profit: float = Field(serialization_alias="totalProfit")
    total_orders: int = Field(serialization_alias="totalOrders")
    average_order_value: float = Field(serialization_alias="averageOrderValue")
    total_customers: int = Field(serialization_alias="totalCustomers")
    units_sold: int = Field(serialization_alias="unitsSold")
    profit_margin: float = Field(serialization_alias="profitMargin")
    return_rate: float = Field(serialization_alias="returnRate")


class AnalyticsRecord(BaseModel):
    """Flexible typed JSON record for dimensional Spark aggregations."""
    model_config = ConfigDict(extra="allow")


class FilterOptions(BaseModel):
    regions: list[str]
    categories: list[str]
    customer_segments: list[str] = Field(default_factory=list)
    sales_channels: list[str] = Field(default_factory=list)
    min_date: date
    max_date: date


class AnalyticsFilters(BaseModel):
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    regions: list[str] = Field(default_factory=list)
    categories: list[str] = Field(default_factory=list)
    customer_segments: list[str] = Field(default_factory=list)
    sales_channels: list[str] = Field(default_factory=list)


class ApiFilters(BaseModel):
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    region: Optional[str] = None
    category: Optional[str] = None
    customer_segment: Optional[str] = None
    sales_channel: Optional[str] = None


class Kpis(BaseModel):
    revenue: float
    profit: float
    orders: int
    units_sold: int
    profit_margin: float
    average_order_value: float


class TrendPoint(BaseModel):
    period: str
    revenue: float
    profit: float
    orders: int


class DimensionMetric(BaseModel):
    name: str
    revenue: float
    profit: float
    orders: int


class Transaction(BaseModel):
    order_id: str
    order_date: date
    region: str
    category: str
    product: str
    customer: str
    quantity: int
    revenue: float
    profit: float


class DashboardResponse(BaseModel):
    filters: FilterOptions
    kpis: Kpis
    revenue_trend: list[TrendPoint]
    category_performance: list[DimensionMetric]
    regional_performance: list[DimensionMetric]
    top_products: list[DimensionMetric]
    transactions: list[Transaction]
