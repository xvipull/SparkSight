"""Route-level contract coverage; Spark calculations are tested by the analytics layer."""
from types import SimpleNamespace

from fastapi.testclient import TestClient

from app.dependencies import get_analytics_service
from app.main import app


class _Frame:
    def limit(self, _: int) -> "_Frame":
        return self

    def count(self) -> int:
        return 1


class _Analytics:
    sales = _Frame()

    @staticmethod
    def get_overview_metrics(*_: object):
        return {"total_revenue": 1000.0, "total_profit": 250.0, "total_orders": 2, "average_order_value": 500.0, "total_customers": 2, "units_sold": 4, "profit_margin": 25.0, "return_rate": 0.0}

    @staticmethod
    def _rows(*_: object, **__: object):
        return [{"category": "Electronics", "revenue": 1000.0, "profit": 250.0, "orders": 2}]

    get_monthly_sales = _rows
    get_monthly_profit = _rows
    get_category_performance = _rows
    get_subcategory_performance = _rows
    get_region_performance = _rows
    get_customer_segments = _rows
    get_sales_channels = _rows
    get_payment_methods = _rows
    get_order_status_distribution = _rows
    get_discount_analysis = _rows

    @staticmethod
    def get_top_products(*_: object, limit: int = 10):
        return _Analytics._rows()[:limit]

    @staticmethod
    def get_top_customers(*_: object, limit: int = 10):
        return _Analytics._rows()[:limit]

    @staticmethod
    def filter_sales(*_: object) -> _Frame:
        return _Frame()


def test_requested_api_endpoints_return_json() -> None:
    app.dependency_overrides[get_analytics_service] = lambda: SimpleNamespace(analytics=_Analytics())
    client = TestClient(app)
    endpoints = [
        "/api/health", "/api/pipeline", "/api/overview", "/api/trends/monthly-sales", "/api/trends/monthly-profit",
        "/api/products/top", "/api/products/categories", "/api/products/subcategories", "/api/customers/top",
        "/api/customers/segments", "/api/regions", "/api/channels", "/api/payment-methods", "/api/order-status",
        "/api/discount-analysis",
    ]
    for endpoint in endpoints:
        response = client.get(endpoint)
        assert response.status_code == 200, response.text
        assert response.headers["content-type"].startswith("application/json")
    assert client.get("/api/overview").json()["totalRevenue"] == 1000.0
    assert client.get("/api/overview?region=South&category=Electronics&customer_segment=Consumer&sales_channel=Online").status_code == 200
    app.dependency_overrides.clear()
