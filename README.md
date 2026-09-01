# SparkSight – Distributed Sales Analytics Platform

SparkSight is a production-style analytics application that turns raw sales transactions into interactive business intelligence. Apache Spark and PySpark handle data quality, feature engineering, and distributed aggregation; FastAPI serves the results; React renders them in a polished, filterable dashboard.

## Overview

SparkSight demonstrates a scalable sales analytics workflow using Apache Spark and PySpark to clean, transform, and aggregate transactional sales data. The application exposes calculated insights through a FastAPI REST API and React analytics application—there are no hardcoded dashboard metrics or charts.

## Features

- Schema-first PySpark ingestion, cleaning, normalization, and financial validation
- Cached Spark DataFrames and reusable aggregation functions
- Global filters for date, region, category, customer segment, and sales channel
- FastAPI REST API with CORS, Pydantic contracts, startup validation, logs, and Swagger docs
- Responsive overview, Products, Customers, Regions, and Data Pipeline views
- Recharts visualizations, professional loading/empty/error states, and Indian currency formatting

## Architecture

```text
sales.csv
   │
   ▼
Apache Spark
   │
   ▼
PySpark ETL
   │
   ▼
Analytics Layer
   │
   ▼
FastAPI REST API
   │
   ▼
React Dashboard
```

## Data Pipeline

1. **Ingestion** — Spark reads `data/sales.csv` with an explicit schema.
2. **Cleaning** — Duplicate transactions are removed; nulls handled; invalid records excluded.
3. **Transformation** — Text values are normalized, categories standardized, and types converted.
4. **Feature engineering** — The pipeline derives time dimensions, discount amount, revenue, profit, and margin.
5. **Aggregation** — Spark calculates dimensional and windowed product, customer, region, channel, and trend analytics.
6. **API** — FastAPI serializes Spark aggregation results as JSON.
7. **Visualization** — React and Recharts render API-sourced metrics and visualizations.

## Analytics Available

- Revenue, profit, orders, units sold, AOV, profit margin, and return rate
- Customers, products, categories, subcategories, regions, and segments
- Sales channels, payment methods, order status, discounts, and monthly trends

## Tech Stack

| Layer | Technology |
| --- | --- |
| Distributed processing | Apache Spark, PySpark |
| Backend | Python, FastAPI, Pydantic |
| Frontend | React, Vite, Tailwind CSS |
| Visualization | Recharts, Lucide React |
| Packaging | Docker, Docker Compose |

## Project Structure

```text
sparksight-sales-analytics/
├── backend/
│   ├── app/               # Spark analytics, transformations, FastAPI routes
│   └── tests/             # API contract tests
├── data/                  # Generated and sample sales data
├── frontend/src/          # React dashboard and reusable components
├── pipeline/              # Batch Parquet curation job
├── scripts/               # Reproducible dataset generator
└── docker-compose.yml
```

## Installation

Prerequisites: Python 3.11+, Java 17+, Node.js 20+, and npm.

```bash
git clone https://github.com/xvipul/SparkSight.git
cd SparkSight/sparksight-sales-analytics
python3.11 -m venv .venv
source .venv/bin/activate
pip install -r backend/requirements.txt
```

On macOS, configure Java 17 before starting Spark:

```bash
export JAVA_HOME="$(/usr/libexec/java_home -v 17)"
```

## Running Backend

```bash
cd sparksight-sales-analytics
source .venv/bin/activate
uvicorn app.main:app --app-dir backend --reload
```

The API runs at `http://localhost:8000`; Swagger docs are at `http://localhost:8000/docs`.

## Running Frontend

```bash
cd sparksight-sales-analytics/frontend
npm install
npm run dev
```

Open `http://localhost:5173`.

## API Endpoints

All applicable analytics endpoints accept optional `start_date`, `end_date`, `region`, `category`, `customer_segment`, and `sales_channel` filters.

| Endpoint | Description |
| --- | --- |
| `GET /api/health` | API and Spark readiness |
| `GET /api/overview` | Core KPI metrics |
| `GET /api/filters` | Available global filter values |
| `GET /api/trends/monthly-sales` | Monthly sales trend |
| `GET /api/trends/monthly-profit` | Monthly profit trend |
| `GET /api/products/summary` | Product KPIs |
| `GET /api/products/top` | Top products with server-side sorting |
| `GET /api/products/categories` | Category performance |
| `GET /api/customers/summary` | Customer KPIs |
| `GET /api/customers/top` | Top customers |
| `GET /api/customers/segments` | Segment performance |
| `GET /api/regions` | Regional performance |
| `GET /api/channels` | Sales channel performance |
| `GET /api/payment-methods` | Payment method analysis |
| `GET /api/order-status` | Order status distribution |
| `GET /api/discount-analysis` | Discount analysis |
| `GET /api/pipeline` | Pipeline health and processed records |

Example: `/api/overview?region=South&category=Electronics`

## Screenshots

Replace these placeholders with product screenshots when publishing:

![SparkSight dashboard](docs/dashboard.png)
![SparkSight products](docs/products.png)
![SparkSight pipeline](docs/pipeline.png)

## Scalability

The included CSV is a local demonstration dataset; SparkSight does not claim to process billions of records in this sample setup. The architecture is deliberately designed so its PySpark transformations and aggregation layer can extend beyond a single machine’s memory with larger distributed datasets and a Spark cluster.

## Future Improvements

- Spark cluster deployment
- AWS S3-backed data lake ingestion
- Databricks notebooks and jobs
- Delta Lake tables and data versioning
- Kafka streaming ingestion
- PostgreSQL for operational metadata and persisted aggregates
- Docker-based CI workflows
- Kubernetes deployment and autoscaling

## Author

`Your Name` — update this placeholder with your name, portfolio, and professional contact details.
