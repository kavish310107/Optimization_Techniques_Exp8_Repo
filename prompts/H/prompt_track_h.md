# Track H Prompt: DBMS Optimization

## 1. Assignment Requirements (Pages 4–5 of Assignment PDF)
- Implement Track H: DBMS Optimization.
- Reference repository had an empty Track H placeholder.
- Requirements:
  - Formulate a representative relational schema and multi-query workload.
  - Implement and compare indexing optimization (B-tree single column, composite covering indexes vs unindexed full table scans).
  - Evaluate query execution plans (`EXPLAIN QUERY PLAN`), execution latency across multiple query archetypes (Point lookups, range filters, multi-table joins, aggregations, low vs high selectivity).
  - Measure write overhead (INSERT / UPDATE latency penalty with secondary indexes) and storage footprint overhead.
  - Formulate query plan / join order optimization (nested loop vs hash/index join, join order re-writing).
  - Ensure 100% equivalence in query results between baseline and optimized approaches.
  - Reproducible dataset generator with fixed seed.
  - Benchmark suite saving machine-readable CSVs and comparison plots in `results/track_h/`.
  - Comprehensive unit test suite in `track H/tests/` verifying schema initialization, data consistency, query plan index usage, result equivalence, and edge cases.

