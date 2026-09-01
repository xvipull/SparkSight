"""Create a deterministic, intentionally imperfect sales dataset for SparkSight.

The resulting raw CSV models line-level transactions.  A handful of blank fields,
duplicates, and category-case variations are deliberately retained for the Spark
data-quality pipeline to detect and correct.
"""
from __future__ import annotations

import csv
import random
from datetime import date, timedelta
from pathlib import Path

SEED = 20250901
TRANSACTION_COUNT = 25_000
ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / "data" / "sales.csv"
FIELDNAMES = [
    "transaction_id", "order_date", "customer_id", "customer_name", "customer_segment",
    "product_id", "product_name", "category", "sub_category", "region", "state", "city",
    "sales_channel", "quantity", "unit_price", "discount", "revenue", "cost", "profit",
    "payment_method", "order_status",
]

LOCATIONS = {
    "North": [("Delhi", "New Delhi"), ("Punjab", "Ludhiana"), ("Uttar Pradesh", "Lucknow")],
    "South": [("Karnataka", "Bengaluru"), ("Tamil Nadu", "Chennai"), ("Telangana", "Hyderabad")],
    "East": [("West Bengal", "Kolkata"), ("Odisha", "Bhubaneswar"), ("Bihar", "Patna")],
    "West": [("Maharashtra", "Mumbai"), ("Gujarat", "Ahmedabad"), ("Rajasthan", "Jaipur")],
    "Central": [("Madhya Pradesh", "Indore"), ("Chhattisgarh", "Raipur"), ("Maharashtra", "Nagpur")],
}
PRODUCTS = [
    ("ELE-101", "Noise-Cancelling Headphones", "Electronics", "Audio", 4999, 0.54),
    ("ELE-102", "Smart LED Television", "Electronics", "Televisions", 38999, 0.68),
    ("ELE-103", "Wireless Keyboard", "Electronics", "Accessories", 1899, 0.43),
    ("ELE-104", "27-inch 4K Monitor", "Electronics", "Monitors", 27999, 0.61),
    ("FUR-101", "Ergonomic Office Chair", "Furniture", "Chairs", 12499, 0.56),
    ("FUR-102", "Solid Wood Desk", "Furniture", "Tables", 21999, 0.64),
    ("FUR-103", "Modular Bookshelf", "Furniture", "Storage", 8999, 0.51),
    ("OFF-101", "Premium Notebook Pack", "Office Supplies", "Paper", 599, 0.28),
    ("OFF-102", "Laser Printer", "Office Supplies", "Machines", 15999, 0.59),
    ("OFF-103", "Gel Pen Set", "Office Supplies", "Writing", 349, 0.25),
    ("CLO-101", "Cotton Formal Shirt", "Clothing", "Menswear", 1799, 0.39),
    ("CLO-102", "Everyday Running Shoes", "Clothing", "Footwear", 3499, 0.48),
    ("CLO-103", "Classic Denim Jacket", "Clothing", "Outerwear", 4299, 0.46),
    ("HAP-101", "Front Load Washing Machine", "Home Appliances", "Laundry", 32999, 0.70),
    ("HAP-102", "Air Fryer", "Home Appliances", "Kitchen", 7499, 0.49),
    ("HAP-103", "Air Purifier", "Home Appliances", "Climate", 11499, 0.57),
]
FIRST_NAMES = ["Aarav", "Aditi", "Arjun", "Diya", "Ishaan", "Kavya", "Meera", "Neha", "Rahul", "Riya", "Saanvi", "Vikram"]
LAST_NAMES = ["Agarwal", "Bose", "Chopra", "Desai", "Gupta", "Iyer", "Kapoor", "Mehta", "Nair", "Patel", "Reddy", "Shah"]
SEGMENTS = ["Consumer", "Corporate", "Small Business", "Enterprise"]
CHANNELS = ["Online", "Retail Store", "Marketplace", "Distributor"]
PAYMENTS = ["UPI", "Credit Card", "Debit Card", "Net Banking", "Cash", "Wallet"]
STATUSES = ["Completed", "Returned", "Cancelled"]


def money(value: float) -> float:
    return round(value, 2)


def make_customers(rng: random.Random, count: int = 4_000) -> list[dict[str, str]]:
    customers = []
    for number in range(1, count + 1):
        segment = rng.choices(SEGMENTS, weights=[55, 22, 16, 7])[0]
        company = f"{rng.choice(LAST_NAMES)} {rng.choice(['Solutions', 'Trading', 'Industries', 'Group'])}"
        name = company if segment in {"Corporate", "Small Business", "Enterprise"} else f"{rng.choice(FIRST_NAMES)} {rng.choice(LAST_NAMES)}"
        customers.append({"customer_id": f"CUS-{number:05d}", "customer_name": name, "customer_segment": segment})
    return customers


def build_record(rng: random.Random, index: int, customers: list[dict[str, str]]) -> dict[str, object]:
    customer = rng.choice(customers)
    product_id, product_name, category, sub_category, base_price, cost_ratio = rng.choice(PRODUCTS)
    region = rng.choice(list(LOCATIONS))
    state, city = rng.choice(LOCATIONS[region])
    segment = customer["customer_segment"]
    channel = rng.choices(CHANNELS, weights=[46, 27, 18, 9])[0]
    status = rng.choices(STATUSES, weights=[91, 6, 3])[0]
    quantity_ceiling = 25 if segment == "Consumer" else (60 if segment == "Small Business" else 150)
    quantity = rng.randint(1, quantity_ceiling)
    unit_price = money(base_price * rng.uniform(0.88, 1.12))
    discount = rng.choices([0, 0.03, 0.05, 0.08, 0.10, 0.15, 0.20], weights=[25, 12, 20, 14, 16, 9, 4])[0]
    if segment == "Enterprise":
        discount = min(0.25, discount + rng.choice([0.03, 0.05, 0.08]))
    revenue = money(quantity * unit_price * (1 - discount))
    cost = money(quantity * unit_price * cost_ratio * rng.uniform(0.94, 1.06))
    profit = money(revenue - cost)
    start_date = date(2023, 1, 1)
    order_date = start_date + timedelta(days=rng.randrange(900))
    return {
        "transaction_id": f"TXN-{index:07d}", "order_date": order_date.isoformat(), **customer,
        "product_id": product_id, "product_name": product_name, "category": category,
        "sub_category": sub_category, "region": region, "state": state, "city": city,
        "sales_channel": channel, "quantity": quantity, "unit_price": unit_price, "discount": discount,
        "revenue": revenue, "cost": cost, "profit": profit,
        "payment_method": rng.choice(PAYMENTS), "order_status": status,
    }


def introduce_quality_issues(rng: random.Random, records: list[dict[str, object]]) -> list[dict[str, object]]:
    """Add <0.2% anomalies without corrupting calculated financial fields."""
    for record in rng.sample(records, 24):
        record[rng.choice(["customer_name", "city", "payment_method"])] = ""
    for record in rng.sample(records, 22):
        record["discount"] = ""
    for record in rng.sample(records, 36):
        category = str(record["category"])
        record["category"] = rng.choice([category.lower(), category.upper(), category.title()])
    duplicates = [record.copy() for record in rng.sample(records, 25)]
    return records + duplicates


def main() -> None:
    rng = random.Random(SEED)
    customers = make_customers(rng)
    records = [build_record(rng, index, customers) for index in range(1, TRANSACTION_COUNT + 1)]
    records = introduce_quality_issues(rng, records)
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    with OUTPUT.open("w", newline="", encoding="utf-8") as csv_file:
        writer = csv.DictWriter(csv_file, fieldnames=FIELDNAMES)
        writer.writeheader()
        writer.writerows(records)
    total_revenue = sum(float(record["revenue"]) for record in records)
    total_profit = sum(float(record["profit"]) for record in records)
    dates = [str(record["order_date"]) for record in records]
    print(f"Records: {len(records):,}")
    print(f"File location: {OUTPUT}")
    print(f"Total revenue: {total_revenue:,.2f}")
    print(f"Total profit: {total_profit:,.2f}")
    print(f"Date range: {min(dates)} to {max(dates)}")


if __name__ == "__main__":
    main()
