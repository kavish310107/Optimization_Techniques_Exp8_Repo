"""
Database Query Plan Analyzer and Cost Estimator.

Extracts SQLite query plans via `EXPLAIN QUERY PLAN` and analyzes:
- Scan Type (SCAN TABLE vs SEARCH TABLE USING INDEX / COVERING INDEX)
- Index usage efficiency
- Approximate cost and estimated b-tree page accesses
"""

import sqlite3
from typing import List, Dict, Any


def get_query_plan(conn: sqlite3.Connection, sql: str) -> List[Dict[str, Any]]:
    """Runs EXPLAIN QUERY PLAN and parses the resulting execution plan nodes."""
    cursor = conn.cursor()
    cursor.execute(f"EXPLAIN QUERY PLAN {sql}")
    rows = cursor.fetchall()
    
    plan_nodes = []
    for row in rows:
        # SQLite returns (id, parent, notused, detail)
        plan_nodes.append({
            "id": row[0],
            "parent": row[1],
            "detail": row[3]
        })
    return plan_nodes


def analyze_index_usage(plan_nodes: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Analyzes execution plan details to determine index utilization and scan strategy."""
    uses_index = False
    uses_covering = False
    scan_tables = []
    search_indexes = []

    for node in plan_nodes:
        detail = node["detail"]
        if "SEARCH" in detail and "USING INDEX" in detail:
            uses_index = True
            search_indexes.append(detail)
        elif "SCAN" in detail:
            scan_tables.append(detail)
        
        if "COVERING INDEX" in detail:
            uses_covering = True

    return {
        "uses_index": uses_index,
        "uses_covering_index": uses_covering,
        "num_scans": len(scan_tables),
        "num_index_searches": len(search_indexes),
        "scan_details": scan_tables,
        "index_details": search_indexes
    }


def get_db_file_size_bytes(db_path: str) -> int:
    """Returns database size in bytes."""
    import os
    if os.path.exists(db_path):
        return os.path.getsize(db_path)
    return 0

