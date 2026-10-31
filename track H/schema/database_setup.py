"""
Database Schema Definition and Synthetic Workload Data Generator.

Implements an E-Commerce relational data model:
1. customers (customer_id, country, signup_date, loyalty_tier, email)
2. categories (category_id, name, department)
3. products (product_id, category_id, price, stock_quantity, rating)
4. orders (order_id, customer_id, order_date, status, total_amount)
5. order_items (item_id, order_id, product_id, quantity, unit_price, discount)

Provides reproducible population with fixed pseudo-random seeds.
"""

import sqlite3
import numpy as np
import os
from typing import Tuple

SCHEMA_DDL = """
PRAGMA foreign_keys = ON;

DROP TABLE IF EXISTS order_items;
DROP TABLE IF EXISTS orders;
DROP TABLE IF EXISTS products;
DROP TABLE IF EXISTS categories;
DROP TABLE IF EXISTS customers;

CREATE TABLE customers (
    customer_id INTEGER PRIMARY KEY,
    name TEXT NOT NULL,
    country TEXT NOT NULL,
    signup_year INTEGER NOT NULL,
    loyalty_tier TEXT NOT NULL,
    credit_score INTEGER NOT NULL
);

CREATE TABLE categories (
    category_id INTEGER PRIMARY KEY,
    name TEXT NOT NULL,
    department TEXT NOT NULL
);

CREATE TABLE products (
    product_id INTEGER PRIMARY KEY,
    category_id INTEGER NOT NULL REFERENCES categories(category_id),
    name TEXT NOT NULL,
    price REAL NOT NULL,
    stock_quantity INTEGER NOT NULL,
    rating REAL NOT NULL
);

CREATE TABLE orders (
    order_id INTEGER PRIMARY KEY,
    customer_id INTEGER NOT NULL REFERENCES customers(customer_id),
    order_date TEXT NOT NULL,
    status TEXT NOT NULL,
    total_amount REAL NOT NULL
);

CREATE TABLE order_items (
    item_id INTEGER PRIMARY KEY,
    order_id INTEGER NOT NULL REFERENCES orders(order_id),
    product_id INTEGER NOT NULL REFERENCES products(product_id),
    quantity INTEGER NOT NULL,
    unit_price REAL NOT NULL,
    discount REAL NOT NULL
);
"""

# Indexes definition for the optimized configuration
OPTIMIZED_INDEXES_DDL = """
-- Point lookup and range query acceleration
CREATE INDEX idx_customers_country_tier ON customers(country, loyalty_tier);
CREATE INDEX idx_products_cat_price ON products(category_id, price);
CREATE INDEX idx_orders_customer_status ON orders(customer_id, status);
CREATE INDEX idx_orders_date ON orders(order_date);
CREATE INDEX idx_order_items_order_id ON order_items(order_id);
CREATE INDEX idx_order_items_product_id ON order_items(product_id);
-- Covering index for order items aggregation queries
CREATE INDEX idx_order_items_covering ON order_items(order_id, product_id, quantity, unit_price, discount);
"""


def init_database(db_path: str, apply_indexes: bool = False) -> sqlite3.Connection:
    """Creates tables in the SQLite database and optionally applies secondary indexes."""
    os.makedirs(os.path.dirname(os.path.abspath(db_path)), exist_ok=True)
    if os.path.exists(db_path):
        os.remove(db_path)
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.executescript(SCHEMA_DDL)
    if apply_indexes:
        cursor.executescript(OPTIMIZED_INDEXES_DDL)
    conn.commit()
    return conn


def populate_database(
    conn: sqlite3.Connection,
    n_customers: int = 5000,
    n_categories: int = 20,
    n_products: int = 1000,
    n_orders: int = 15000,
    avg_items_per_order: int = 3,
    seed: int = 42
) -> Tuple[int, int, int, int, int]:
    """Generates synthetic data and inserts records in batch for high reproducibility."""
    rng = np.random.default_rng(seed)
    cursor = conn.cursor()

    # 1. Customers
    countries = ["US", "DE", "IN", "UK", "FR", "JP", "CA", "BR"]
    tiers = ["Bronze", "Silver", "Gold", "Platinum"]
    tier_probs = [0.50, 0.30, 0.15, 0.05]

    customers_data = [
        (
            cid,
            f"Customer_{cid}",
            str(rng.choice(countries)),
            int(rng.integers(2018, 2026)),
            str(rng.choice(tiers, p=tier_probs)),
            int(rng.integers(300, 850))
        )
        for cid in range(1, n_customers + 1)
    ]
    cursor.executemany("INSERT INTO customers VALUES (?, ?, ?, ?, ?, ?)", customers_data)

    # 2. Categories
    departments = ["Electronics", "Apparel", "Home", "Books", "Sports"]
    categories_data = [
        (cat_id, f"Category_{cat_id}", str(rng.choice(departments)))
        for cat_id in range(1, n_categories + 1)
    ]
    cursor.executemany("INSERT INTO categories VALUES (?, ?, ?)", categories_data)

    # 3. Products
    products_data = [
        (
            pid,
            int(rng.integers(1, n_categories + 1)),
            f"Product_{pid}",
            round(float(rng.uniform(5.0, 500.0)), 2),
            int(rng.integers(0, 1000)),
            round(float(rng.uniform(1.0, 5.0)), 1)
        )
        for pid in range(1, n_products + 1)
    ]
    cursor.executemany("INSERT INTO products VALUES (?, ?, ?, ?, ?, ?)", products_data)

    # 4. Orders
    statuses = ["Pending", "Processing", "Shipped", "Delivered", "Cancelled"]
    status_probs = [0.05, 0.10, 0.20, 0.60, 0.05]

    orders_data = []
    for oid in range(1, n_orders + 1):
        cid = int(rng.integers(1, n_customers + 1))
        # Random date between 2022-01-01 and 2026-01-01
        days_offset = int(rng.integers(0, 1460))
        year = 2022 + days_offset // 365
        month = 1 + (days_offset % 365) // 30
        day = 1 + (days_offset % 30)
        date_str = f"{year:04d}-{min(month, 12):02d}-{min(day, 28):02d}"
        status = str(rng.choice(statuses, p=status_probs))
        total_amt = round(float(rng.uniform(15.0, 1200.0)), 2)
        orders_data.append((oid, cid, date_str, status, total_amt))

    cursor.executemany("INSERT INTO orders VALUES (?, ?, ?, ?, ?)", orders_data)

    # 5. Order Items
    order_items_data = []
    item_id = 1
    for oid in range(1, n_orders + 1):
        num_items = int(rng.integers(1, avg_items_per_order * 2))
        for _ in range(num_items):
            pid = int(rng.integers(1, n_products + 1))
            qty = int(rng.integers(1, 5))
            price = products_data[pid - 1][3]
            discount = round(float(rng.choice([0.0, 0.05, 0.10, 0.15, 0.20])), 2)
            order_items_data.append((item_id, oid, pid, qty, price, discount))
            item_id += 1

    cursor.executemany("INSERT INTO order_items VALUES (?, ?, ?, ?, ?, ?)", order_items_data)

    conn.commit()
    return len(customers_data), len(categories_data), len(products_data), len(orders_data), len(order_items_data)


def apply_indexes_to_db(conn: sqlite3.Connection):
    """Applies the optimized index set to an existing populated database."""
    conn.executescript(OPTIMIZED_INDEXES_DDL)
    conn.commit()


def drop_indexes_from_db(conn: sqlite3.Connection):
    """Drops all non-primary key secondary indexes."""
    cursor = conn.cursor()
    cursor.execute("SELECT name FROM sqlite_master WHERE type='index' AND name NOT LIKE 'sqlite_autoindex%';")
    indexes = cursor.fetchall()
    for (idx_name,) in indexes:
        cursor.execute(f"DROP INDEX IF EXISTS {idx_name};")
    conn.commit()

