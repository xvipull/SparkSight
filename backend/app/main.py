"""FastAPI application for the SparkSight distributed analytics platform."""
from __future__ import annotations

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import get_settings
from app.dependencies import get_analytics_service
from app.routes.analytics import router as analytics_router
from app.spark_session import get_spark_session, stop_spark_session

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s [%(name)s] %(message)s")
logger = logging.getLogger(__name__)
settings = get_settings()


@asynccontextmanager
async def lifespan(_: FastAPI):
    """Fail early when Spark or the source data cannot support the API."""
    logger.info("Validating SparkSight analytics startup dependencies")
    get_spark_session()
    service = get_analytics_service()
    service.analytics.sales.limit(1).count()
    logger.info("SparkSight startup validation completed")
    yield
    stop_spark_session()
    logger.info("SparkSight SparkSession stopped")


app = FastAPI(
    title="SparkSight API",
    description="Production-style REST API backed by Apache Spark sales aggregations.",
    version="1.0.0",
    lifespan=lifespan,
)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["GET"],
    allow_headers=["*"],
)
app.include_router(analytics_router)
