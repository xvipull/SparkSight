"""Application-scoped dependencies shared by FastAPI route modules."""
from datetime import date
from typing import Optional

from fastapi import Query

from app.schemas import ApiFilters
from app.services.spark_service import SalesAnalyticsService

analytics_service = SalesAnalyticsService()


def get_analytics_service() -> SalesAnalyticsService:
    return analytics_service


def get_api_filters(
    start_date: Optional[date] = Query(default=None), end_date: Optional[date] = Query(default=None),
    region: Optional[str] = Query(default=None), category: Optional[str] = Query(default=None),
    customer_segment: Optional[str] = Query(default=None), sales_channel: Optional[str] = Query(default=None),
) -> ApiFilters:
    """Parse all optional API filters once so every endpoint shares the same contract."""
    return ApiFilters(start_date=start_date, end_date=end_date, region=region, category=category, customer_segment=customer_segment, sales_channel=sales_channel)
