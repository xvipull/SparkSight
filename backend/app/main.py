from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import get_settings
from app.schemas import AnalyticsFilters, DashboardResponse, FilterOptions
from app.services.spark_service import SalesAnalyticsService, get_spark

settings = get_settings()
analytics = SalesAnalyticsService()


@asynccontextmanager
async def lifespan(_: FastAPI):
    get_spark()
    yield
    get_spark().stop()


app = FastAPI(title="SparkSight API", description="Apache Spark-powered sales analytics for SparkSight.", version="1.0.0", lifespan=lifespan)
app.add_middleware(CORSMiddleware, allow_origins=settings.cors_origins, allow_credentials=True, allow_methods=["GET"], allow_headers=["*"])


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "healthy", "service": "SparkSight API"}


@app.get("/api/v1/filters", response_model=FilterOptions, tags=["SparkSight Analytics"])
def filters() -> FilterOptions:
    return analytics.filter_options()


@app.get("/api/v1/dashboard", response_model=DashboardResponse, tags=["SparkSight Analytics"])
def dashboard(start_date: str | None = None, end_date: str | None = None, regions: list[str] = Query(default=[]), categories: list[str] = Query(default=[])) -> DashboardResponse:
    try:
        return analytics.dashboard(AnalyticsFilters(start_date=start_date, end_date=end_date, regions=regions, categories=categories))
    except FileNotFoundError as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc
