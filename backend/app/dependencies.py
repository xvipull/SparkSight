"""Application-scoped dependencies shared by FastAPI route modules."""
from app.services.spark_service import SalesAnalyticsService

analytics_service = SalesAnalyticsService()


def get_analytics_service() -> SalesAnalyticsService:
    return analytics_service
