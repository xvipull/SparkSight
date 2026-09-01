"""Shared SparkSession lifecycle for SparkSight services."""
from __future__ import annotations

import logging
from functools import lru_cache

from pyspark.sql import SparkSession

from app.core.config import get_settings

logger = logging.getLogger(__name__)


@lru_cache
def get_spark_session() -> SparkSession:
    """Create one configured SparkSession for the process and reuse it."""
    settings = get_settings()
    try:
        spark = (
            SparkSession.builder.appName("SparkSight Data Engineering")
            .master(settings.spark_master)
            .config("spark.ui.enabled", "false")
            .config("spark.sql.session.timeZone", "UTC")
            .config("spark.sql.shuffle.partitions", "8")
            .getOrCreate()
        )
        spark.sparkContext.setLogLevel("WARN")
        logger.info("SparkSight SparkSession started with master=%s", settings.spark_master)
        return spark
    except Exception as exc:  # pragma: no cover - environment-specific Spark failures
        logger.exception("Unable to create SparkSession")
        raise RuntimeError("SparkSight could not initialize Apache Spark") from exc


def stop_spark_session() -> None:
    """Stop the shared session during application shutdown."""
    if get_spark_session.cache_info().currsize:
        get_spark_session().stop()
        get_spark_session.cache_clear()
