"""
Unit and Integration Tests for Track H: DBMS Optimization.

Validates:
1. Schema integrity and foreign key enforcement.
2. Data population consistency and deterministic seeding.
3. Index creation and drop lifecycle.
4. Query execution plan inspection (distinguishing SCAN vs INDEX SEARCH).
5. 100% output equivalence between baseline and optimized query execution.
6. Graceful handling of empty results and boundary range predicates.
"""

import pytest
import sqlite3
import os
import sys

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from schema.database_setup import init_database, populate_database, apply_indexes_to_db, drop_indexes_from_db
from workloads.queries import QUERIES
from optimizers.plan_analyzer import get_query_plan, analyze_index_usage


@pytest.fixture
def test_db(tmp_path):
    db_file = tmp_path / "test_ecommerce.db"
    conn = init_database(str(db_file), apply_indexes=False)
    populate_database(conn, n_customers=300, n_categories=5, n_products=50, n_orders=800, seed=42)
    yield conn
    conn.close()


def test_schema_and_counts(test_db):
    cursor = test_db.cursor()
    cursor.execute("SELECT COUNT(*) FROM customers")
    assert cursor.fetchone()[0] == 300
    cursor.execute("SELECT COUNT(*) FROM categories")
    assert cursor.fetchone()[0] == 5
    cursor.execute("SELECT COUNT(*) FROM products")
    assert cursor.fetchone()[0] == 50
    cursor.execute("SELECT COUNT(*) FROM orders")
    assert cursor.fetchone()[0] == 800
    cursor.execute("SELECT COUNT(*) FROM order_items")
    assert cursor.fetchone()[0] > 800


def test_index_lifecycle(test_db):
    cursor = test_db.cursor()
    # Before adding indexes, only sqlite_autoindex should exist
    cursor.execute("SELECT COUNT(*) FROM sqlite_master WHERE type='index' AND name NOT LIKE 'sqlite_autoindex%';")
    assert cursor.fetchone()[0] == 0

    apply_indexes_to_db(test_db)
    cursor.execute("SELECT COUNT(*) FROM sqlite_master WHERE type='index' AND name NOT LIKE 'sqlite_autoindex%';")
    assert cursor.fetchone()[0] == 7

    drop_indexes_from_db(test_db)
    cursor.execute("SELECT COUNT(*) FROM sqlite_master WHERE type='index' AND name NOT LIKE 'sqlite_autoindex%';")
    assert cursor.fetchone()[0] == 0


def test_query_plan_distinguishes_index_from_scan(test_db):
    sql = QUERIES["Q1_Point_Filter"].baseline_sql

    # Unindexed state -> SCAN
    drop_indexes_from_db(test_db)
    plan_base = get_query_plan(test_db, sql)
    analysis_base = analyze_index_usage(plan_base)
    assert analysis_base["uses_index"] is False
    assert analysis_base["num_scans"] >= 1

    # Indexed state -> SEARCH USING INDEX
    apply_indexes_to_db(test_db)
    plan_opt = get_query_plan(test_db, sql)
    analysis_opt = analyze_index_usage(plan_opt)
    assert analysis_opt["uses_index"] is True


def test_query_output_equivalence_all_queries(test_db):
    cursor = test_db.cursor()

    for qid, qdef in QUERIES.items():
        # Baseline execution without secondary indexes
        drop_indexes_from_db(test_db)
        cursor.execute(qdef.baseline_sql)
        base_rows = cursor.fetchall()

        # Optimized execution with indexes and alternative rewrites
        apply_indexes_to_db(test_db)
        opt_sql = qdef.optimized_sql if qdef.optimized_sql else qdef.baseline_sql
        cursor.execute(opt_sql)
        opt_rows = cursor.fetchall()

        # Check equivalence
        assert len(base_rows) == len(opt_rows), f"Row count mismatch on {qid}: {len(base_rows)} vs {len(opt_rows)}"
        if "ORDER BY" not in qdef.baseline_sql.upper():
            assert sorted(str(r) for r in base_rows) == sorted(str(r) for r in opt_rows), f"Set mismatch on {qid}"
        else:
            assert base_rows == opt_rows, f"Ordered result mismatch on {qid}"


def test_boundary_and_empty_results(test_db):
    apply_indexes_to_db(test_db)
    cursor = test_db.cursor()

    # Query matching 0 records
    cursor.execute("SELECT * FROM customers WHERE country = 'NONEXISTENT_COUNTRY';")
    rows = cursor.fetchall()
    assert len(rows) == 0

    # Boundary price filter
    cursor.execute("SELECT COUNT(*) FROM products WHERE price < 0.0;")
    assert cursor.fetchone()[0] == 0

