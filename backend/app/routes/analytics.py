"""REST endpoints exposing real Apache Spark analytics."""
from __future__ import annotations

import logging
from typing import Any, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status

from app.dependencies import get_analytics_service
from app.schemas import AnalyticsFilters, AnalyticsRecord, DashboardResponse, FilterOptions, HealthResponse, OverviewResponse, PipelineStatusResponse
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


@router.get("/overview", response_model=OverviewResponse, summary="Get top-level sales metrics")
def overview(service: SalesAnalyticsService = Depends(get_analytics_service)) -> OverviewResponse:
    try:
        metrics = service.analytics.get_overview_metrics()
        return OverviewResponse(**metrics)
    except Exception as exc:
        raise _analytics_error("building overview metrics", exc) from exc


def _list(operation: str, callback: Any) -> list[AnalyticsRecord]:
    try:
        return [AnalyticsRecord.model_validate(item) for item in callback()]
    except Exception as exc:
        raise _analytics_error(operation, exc) from exc


@router.get("/trends/monthly-sales", response_model=list[AnalyticsRecord])
def monthly_sales(service: SalesAnalyticsService = Depends(get_analytics_service)) -> list[AnalyticsRecord]:
    return _list("building monthly sales", service.analytics.get_monthly_sales)


@router.get("/trends/monthly-profit", response_model=list[AnalyticsRecord])
def monthly_profit(service: SalesAnalyticsService = Depends(get_analytics_service)) -> list[AnalyticsRecord]:
    return _list("building monthly profit", service.analytics.get_monthly_profit)


@router.get("/products/top", response_model=list[AnalyticsRecord])
def top_products(limit: int = Query(default=10, ge=1, le=50), service: SalesAnalyticsService = Depends(get_analytics_service)) -> list[AnalyticsRecord]:
    return _list("building top products", lambda: service.analytics.get_top_products(limit=limit))


@router.get("/products/categories", response_model=list[AnalyticsRecord])
def categories(service: SalesAnalyticsService = Depends(get_analytics_service)) -> list[AnalyticsRecord]:
    return _list("building category performance", service.analytics.get_category_performance)


@router.get("/products/subcategories", response_model=list[AnalyticsRecord])
def subcategories(service: SalesAnalyticsService = Depends(get_analytics_service)) -> list[AnalyticsRecord]:
    return _list("building subcategory performance", service.analytics.get_subcategory_performance)


@router.get("/customers/top", response_model=list[AnalyticsRecord])
def top_customers(limit: int = Query(default=10, ge=1, le=50), service: SalesAnalyticsService = Depends(get_analytics_service)) -> list[AnalyticsRecord]:
    return _list("building top customers", lambda: service.analytics.get_top_customers(limit=limit))


@router.get("/customers/segments", response_model=list[AnalyticsRecord])
def customer_segments(service: SalesAnalyticsService = Depends(get_analytics_service)) -> list[AnalyticsRecord]:
    return _list("building customer segments", service.analytics.get_customer_segments)


@router.get("/regions", response_model=list[AnalyticsRecord])
def regions(service: SalesAnalyticsService = Depends(get_analytics_service)) -> list[AnalyticsRecord]:
    return _list("building regional performance", service.analytics.get_region_performance)


@router.get("/channels", response_model=list[AnalyticsRecord])
def channels(service: SalesAnalyticsService = Depends(get_analytics_service)) -> list[AnalyticsRecord]:
    return _list("building sales channel performance", service.analytics.get_sales_channels)


@router.get("/payment-methods", response_model=list[AnalyticsRecord])
def payment_methods(service: SalesAnalyticsService = Depends(get_analytics_service)) -> list[AnalyticsRecord]:
    return _list("building payment-method performance", service.analytics.get_payment_methods)


@router.get("/order-status", response_model=list[AnalyticsRecord])
def order_status(service: SalesAnalyticsService = Depends(get_analytics_service)) -> list[AnalyticsRecord]:
    return _list("building order-status distribution", service.analytics.get_order_status_distribution)


@router.get("/discount-analysis", response_model=list[AnalyticsRecord])
def discount_analysis(service: SalesAnalyticsService = Depends(get_analytics_service)) -> list[AnalyticsRecord]:
    return _list("building discount analysis", service.analytics.get_discount_analysis)


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
