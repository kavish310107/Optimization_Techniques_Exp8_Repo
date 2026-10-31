"""
Workload Query Suite for Database Optimization.

Covers 6 distinct query archetypes:
Q1. Point / Filter Lookup (Customer by country & loyalty tier)
Q2. Range Filter & Projection (Products in category within price bounds)
Q3. Two-Table Foreign-Key Join (Orders for specific customer status)
Q4. Complex Multi-Table Join & Aggregation (Top revenue categories by country)
Q5. Covering Index Aggregation (Order items quantity and discount summary)
Q6. Subquery / Join Order Alternative (High-spending customers with recent delivered orders)
"""

from dataclasses import dataclass
from typing import Dict, List, Optional


@dataclass
class QueryDefinition:
    qid: str
    name: str
    description: str
    baseline_sql: str
    optimized_sql: Optional[str] = None # Query rewrite / join order reordering alternative


QUERIES: Dict[str, QueryDefinition] = {
    "Q1_Point_Filter": QueryDefinition(
        qid="Q1",
        name="Customer Loyalty Point Filter",
        description="Filter customers by high-selectivity compound predicate (country = 'DE' and loyalty_tier = 'Platinum').",
        baseline_sql="""
            SELECT customer_id, name, credit_score 
            FROM customers 
            WHERE country = 'DE' AND loyalty_tier = 'Platinum';
        """
    ),
    "Q2_Range_Filter": QueryDefinition(
        qid="Q2",
        name="Category Price Range Filter",
        description="Range query retrieving active products in specific category within price bounds ($50-$200).",
        baseline_sql="""
            SELECT product_id, name, price, stock_quantity 
            FROM products 
            WHERE category_id = 7 AND price BETWEEN 50.0 AND 200.0;
        """
    ),
    "Q3_Two_Table_Join": QueryDefinition(
        qid="Q3",
        name="Customer Order Status Join",
        description="Retrieve all Delivered orders for customers in United States.",
        baseline_sql="""
            SELECT c.customer_id, c.name, o.order_id, o.order_date, o.total_amount
            FROM customers c
            JOIN orders o ON c.customer_id = o.customer_id
            WHERE c.country = 'US' AND o.status = 'Delivered';
        """
    ),
    "Q4_Multi_Table_Aggregation": QueryDefinition(
        qid="Q4",
        name="Cross-Department Revenue Analysis",
        description="Complex 4-table join calculating category-level gross revenue from shipped orders.",
        baseline_sql="""
            SELECT cat.name AS category_name, 
                   COUNT(DISTINCT o.order_id) AS total_orders, 
                   SUM(oi.quantity * oi.unit_price * (1.0 - oi.discount)) AS gross_revenue
            FROM orders o
            JOIN order_items oi ON o.order_id = oi.order_id
            JOIN products p ON oi.product_id = p.product_id
            JOIN categories cat ON p.category_id = cat.category_id
            WHERE o.status IN ('Shipped', 'Delivered')
            GROUP BY cat.category_id, cat.name
            ORDER BY gross_revenue DESC;
        """
    ),
    "Q5_Covering_Index_Agg": QueryDefinition(
        qid="Q5",
        name="Order Items Financial Rollup",
        description="Calculates volume and discount aggregations across item lines. Uses covering index.",
        baseline_sql="""
            SELECT product_id, 
                   SUM(quantity) AS total_units, 
                   AVG(discount) AS mean_discount,
                   SUM(quantity * unit_price) AS raw_value
            FROM order_items
            GROUP BY product_id
            HAVING total_units > 10;
        """
    ),
    "Q6_Join_Order_Rewrite": QueryDefinition(
        qid="Q6",
        name="Subquery vs Join Order Optimization",
        description="Finds customers who placed high-value orders in 2024. Compares correlated subquery against flattened inner join.",
        # Unoptimized baseline: Subquery inside IN clause
        baseline_sql="""
            SELECT c.customer_id, c.name, c.loyalty_tier
            FROM customers c
            WHERE c.customer_id IN (
                SELECT o.customer_id
                FROM orders o
                WHERE o.order_date >= '2024-01-01' 
                  AND o.total_amount > 800.0 
                  AND o.status = 'Delivered'
            )
            ORDER BY c.customer_id;
        """,
        # Optimized rewrite: Explicit filtered JOIN with early projection
        optimized_sql="""
            SELECT DISTINCT c.customer_id, c.name, c.loyalty_tier
            FROM (
                SELECT customer_id
                FROM orders
                WHERE order_date >= '2024-01-01' 
                  AND total_amount > 800.0 
                  AND status = 'Delivered'
            ) o_filt
            JOIN customers c ON c.customer_id = o_filt.customer_id
            ORDER BY c.customer_id;
        """
    )
}

