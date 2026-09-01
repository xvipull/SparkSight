"""REST endpoints exposing real Apache Spark analytics."""
from __future__ import annotations

import logging
from typing import Any, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status

from app.dependencies import get_analytics_service, get_api_filters
from app.schemas import AnalyticsFilters, AnalyticsRecord, ApiFilters, DashboardResponse, FilterOptions, HealthResponse, OverviewResponse, PipelineStatusResponse
from app.services.spark_service import SalesAnalyticsService

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api", tags=["SparkSight Analytics"])


def _analytics_error(operation: str, exc: Exception) -> HTTPException:
    logger.exception("Spark analytics failed while %s", operation)
    return HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=f"SparkSight analytics are temporarily unavailable while {operation}.")


@router.get("/health", response_model=HealthResponse, summary="Check API and Spark service readiness")
def health(service: SalesAnalyticsService = Depends(get_analytics_service)) -> HealthResponse:
    try:
        service.analytics.sales.limit(1).count()
        return HealthResponse(status="healthy", service="SparkSight API", analytics_engine="Apache Spark")
    except Exception as exc:
        raise _analytics_error("checking service health", exc) from exc


@router.get("/pipeline", response_model=PipelineStatusResponse, summary="Get distributed pipeline status and processed record count")
def pipeline_status(service: SalesAnalyticsService = Depends(get_analytics_service)) -> PipelineStatusResponse:
    try:
        return PipelineStatusResponse(status="healthy", records_processed=service.analytics.sales.count(), data_source="sales.csv", processing_engine="Apache Spark", api="FastAPI", frontend="React")
    except Exception as exc:
        raise _analytics_error("checking pipeline status", exc) from exc


@router.get("/filters", response_model=FilterOptions, summary="List valid global analytics filters")
def filter_options(service: SalesAnalyticsService = Depends(get_analytics_service)) -> FilterOptions:
    try:
        return service.filter_options()
    except Exception as exc:
        raise _analytics_error("loading global filters", exc) from exc


@router.get("/overview", response_model=OverviewResponse, summary="Get top-level sales metrics")
def overview(filters: ApiFilters = Depends(get_api_filters), service: SalesAnalyticsService = Depends(get_analytics_service)) -> OverviewResponse:
    try:
        metrics = service.analytics.get_overview_metrics(service.analytics.filter_sales(filters))
        return OverviewResponse(**metrics)
    except Exception as exc:
        raise _analytics_error("building overview metrics", exc) from exc


def _list(operation: str, callback: Any) -> list[AnalyticsRecord]:
    try:
        return [AnalyticsRecord.model_validate(item) for item in callback()]
    except Exception as exc:
        raise _analytics_error(operation, exc) from exc


@router.get("/trends/monthly-sales", response_model=list[AnalyticsRecord])
def monthly_sales(filters: ApiFilters = Depends(get_api_filters), service: SalesAnalyticsService = Depends(get_analytics_service)) -> list[AnalyticsRecord]:
    return _list("building monthly sales", lambda: service.analytics.get_monthly_sales(service.analytics.filter_sales(filters)))


@router.get("/trends/monthly-profit", response_model=list[AnalyticsRecord])
def monthly_profit(filters: ApiFilters = Depends(get_api_filters), service: SalesAnalyticsService = Depends(get_analytics_service)) -> list[AnalyticsRecord]:
    return _list("building monthly profit", lambda: service.analytics.get_monthly_profit(service.analytics.filter_sales(filters)))


@router.get("/products/top", response_model=list[AnalyticsRecord])
def top_products(limit: int = Query(default=10, ge=1, le=50), sort_by: str = Query(default="revenue", pattern="^(revenue|profit|units_sold)$"), filters: ApiFilters = Depends(get_api_filters), service: SalesAnalyticsService = Depends(get_analytics_service)) -> list[AnalyticsRecord]:
    return _list("building top products", lambda: service.analytics.get_top_products(service.analytics.filter_sales(filters), limit=limit, sort_by=sort_by))


@router.get("/products/summary", response_model=AnalyticsRecord)
def product_summary(filters: ApiFilters = Depends(get_api_filters), service: SalesAnalyticsService = Depends(get_analytics_service)) -> AnalyticsRecord:
    return AnalyticsRecord.model_validate(service.analytics.get_product_summary(service.analytics.filter_sales(filters)))


@router.get("/products/categories", response_model=list[AnalyticsRecord])
def categories(filters: ApiFilters = Depends(get_api_filters), service: SalesAnalyticsService = Depends(get_analytics_service)) -> list[AnalyticsRecord]:
    return _list("building category performance", lambda: service.analytics.get_category_performance(service.analytics.filter_sales(filters)))


@router.get("/products/subcategories", response_model=list[AnalyticsRecord])
def subcategories(filters: ApiFilters = Depends(get_api_filters), service: SalesAnalyticsService = Depends(get_analytics_service)) -> list[AnalyticsRecord]:
    return _list("building subcategory performance", lambda: service.analytics.get_subcategory_performance(service.analytics.filter_sales(filters)))


@router.get("/customers/top", response_model=list[AnalyticsRecord])
def top_customers(limit: int = Query(default=10, ge=1, le=50), filters: ApiFilters = Depends(get_api_filters), service: SalesAnalyticsService = Depends(get_analytics_service)) -> list[AnalyticsRecord]:
    return _list("building top customers", lambda: service.analytics.get_top_customers(service.analytics.filter_sales(filters), limit=limit))


@router.get("/customers/summary", response_model=AnalyticsRecord)
def customer_summary(filters: ApiFilters = Depends(get_api_filters), service: SalesAnalyticsService = Depends(get_analytics_service)) -> AnalyticsRecord:
    return AnalyticsRecord.model_validate(service.analytics.get_customer_summary(service.analytics.filter_sales(filters)))


@router.get("/customers/segments", response_model=list[AnalyticsRecord])
def customer_segments(filters: ApiFilters = Depends(get_api_filters), service: SalesAnalyticsService = Depends(get_analytics_service)) -> list[AnalyticsRecord]:
    return _list("building customer segments", lambda: service.analytics.get_customer_segments(service.analytics.filter_sales(filters)))


@router.get("/regions", response_model=list[AnalyticsRecord])
def regions(filters: ApiFilters = Depends(get_api_filters), service: SalesAnalyticsService = Depends(get_analytics_service)) -> list[AnalyticsRecord]:
    return _list("building regional performance", lambda: service.analytics.get_region_performance(service.analytics.filter_sales(filters)))


@router.get("/channels", response_model=list[AnalyticsRecord])
def channels(filters: ApiFilters = Depends(get_api_filters), service: SalesAnalyticsService = Depends(get_analytics_service)) -> list[AnalyticsRecord]:
    return _list("building sales channel performance", lambda: service.analytics.get_sales_channels(service.analytics.filter_sales(filters)))


@router.get("/payment-methods", response_model=list[AnalyticsRecord])
def payment_methods(filters: ApiFilters = Depends(get_api_filters), service: SalesAnalyticsService = Depends(get_analytics_service)) -> list[AnalyticsRecord]:
    return _list("building payment-method performance", lambda: service.analytics.get_payment_methods(service.analytics.filter_sales(filters)))


@router.get("/order-status", response_model=list[AnalyticsRecord])
def order_status(filters: ApiFilters = Depends(get_api_filters), service: SalesAnalyticsService = Depends(get_analytics_service)) -> list[AnalyticsRecord]:
    return _list("building order-status distribution", lambda: service.analytics.get_order_status_distribution(service.analytics.filter_sales(filters)))


@router.get("/discount-analysis", response_model=list[AnalyticsRecord])
def discount_analysis(filters: ApiFilters = Depends(get_api_filters), service: SalesAnalyticsService = Depends(get_analytics_service)) -> list[AnalyticsRecord]:
    return _list("building discount analysis", lambda: service.analytics.get_discount_analysis(service.analytics.filter_sales(filters)))


# Dashboard endpoints remain available for the existing React experience while the
# resource-oriented endpoints above serve dedicated consumers.
@router.get("/v1/filters", response_model=FilterOptions, include_in_schema=False)
def dashboard_filters(service: SalesAnalyticsService = Depends(get_analytics_service)) -> FilterOptions:
    try:
        return service.filter_options()
    except Exception as exc:
        raise _analytics_error("loading dashboard filters", exc) from exc


@router.get("/v1/dashboard", response_model=DashboardResponse, include_in_schema=False)
def dashboard(
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    regions: list[str] = Query(default=[]),
    categories: list[str] = Query(default=[]),
    service: SalesAnalyticsService = Depends(get_analytics_service),
) -> DashboardResponse:
    try:
        filters = AnalyticsFilters(start_date=start_date, end_date=end_date, regions=regions, categories=categories)
        return service.dashboard(filters)
    except Exception as exc:
        raise _analytics_error("building dashboard analytics", exc) from exc
