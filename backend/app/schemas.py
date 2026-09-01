from datetime import date
from pydantic import BaseModel, Field


class FilterOptions(BaseModel):
    regions: list[str]
    categories: list[str]
    min_date: date
    max_date: date


class AnalyticsFilters(BaseModel):
    start_date: date | None = None
    end_date: date | None = None
    regions: list[str] = Field(default_factory=list)
    categories: list[str] = Field(default_factory=list)


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
