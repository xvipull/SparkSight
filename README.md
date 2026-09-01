# SparkSight – Distributed Sales Analytics Platform

SparkSight is a full-stack sales analytics project in which Apache Spark calculates every dashboard value. FastAPI exposes the computed results and a React dashboard renders them with Recharts. No dashboard KPI or chart contains hardcoded business data.

## Architecture

```text
data/sales_transactions.csv
          │
          ├── pipeline/transform_sales.py → partitioned Parquet (batch workflow)
          │
          └── PySpark transformations → FastAPI /api/v1/dashboard → React + Recharts
```

## What Spark computes

- Net revenue: `unit_price × quantity × (1 - discount)`
- Profit: net revenue minus unit cost × quantity
- KPI totals, profit margin, average order value, monthly trends
- Product, category, and regional groupings
- Filtered transactions, controlled by date, region, and category query parameters

## Quick start

Prerequisites: Python 3.11+, Java 17+, and Node 20+.

```bash
cd sparksight-sales-analytics
python -m venv .venv
source .venv/bin/activate
pip install -r backend/requirements.txt
uvicorn app.main:app --app-dir backend --reload
```

In a second terminal:

```bash
cd sparksight-sales-analytics/frontend
npm install
npm run dev
```

Open `http://localhost:5173`. Interactive API documentation is at `http://localhost:8000/docs` and uses the SparkSight API title.

## Docker

```bash
cd sparksight-sales-analytics
docker compose up --build
```

The dashboard is then available at `http://localhost:5173`; the API is at `http://localhost:8000`.

## Batch pipeline

To materialize the curated, partitioned Parquet dataset:

```bash
cd sparksight-sales-analytics
python pipeline/transform_sales.py
```

## API

| Endpoint | Purpose |
| --- | --- |
| `GET /health` | SparkSight API health check |
| `GET /api/v1/filters` | Available date, region, and category filters |
| `GET /api/v1/dashboard` | All computed dashboard data |

`/api/v1/dashboard` accepts optional `start_date`, `end_date`, repeated `regions`, and repeated `categories` query values. For example: `/api/v1/dashboard?regions=North&regions=West&categories=Electronics`.

## Project layout

```text
sparksight-sales-analytics/
├── backend/             # FastAPI service and PySpark transformations
├── data/                # Source sales transactions
├── frontend/            # Vite + React + Tailwind + Recharts dashboard
├── pipeline/            # Batch Spark curation job
└── docker-compose.yml
```
