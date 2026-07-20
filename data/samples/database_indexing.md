# Basics of Database Indexing

A database index is an auxiliary data structure that lets the query engine
find rows matching a condition without scanning the entire table. Without
an index, a query like `WHERE user_id = 42` requires a full table scan —
reading every row and checking the condition, which is O(n) in the number
of rows.

## The B-Tree Index

Most relational databases default to a B-tree (or B+tree) index. It keeps
keys in sorted order across a balanced tree of fixed-size pages, so lookups,
range scans, and ordered iteration are all efficient — typically O(log n)
for a point lookup. Because the tree stays balanced under inserts and
deletes, performance is predictable even as the table grows.

## What Gets Indexed

An index is built on one or more columns. A composite index on `(a, b)`
speeds up queries that filter on `a` alone or on `a` and `b` together, but
generally not queries that filter on `b` alone — the leftmost column(s)
must be part of the filter for the index to be usable. This is why column
order in a composite index matters.

## The Cost of Indexes

Indexes are not free. Every index:

- Takes additional disk space, roughly proportional to the indexed columns'
  size times the row count.
- Slows down writes, because every `INSERT`, `UPDATE`, or `DELETE` must also
  update each index on the affected columns.
- Can become a bottleneck if over-used on write-heavy tables.

This is why indexing is a trade-off: index the columns that are actually
used in `WHERE`, `JOIN`, and `ORDER BY` clauses of frequent queries, not
every column defensively.

## Other Index Types

- **Hash index**: O(1) average lookup for exact-match equality, but useless
  for range queries since it discards ordering.
- **Covering index**: includes every column a query needs, so the engine
  can answer the query from the index alone without touching the table.
- **Full-text / inverted index**: maps tokens to the documents/rows that
  contain them, used for text search rather than exact-match filtering.

## Reading a Query Plan

Most databases expose an `EXPLAIN` (or `EXPLAIN ANALYZE`) command that shows
whether a query used an index scan or fell back to a sequential scan. This
is the standard first step when diagnosing a slow query.
