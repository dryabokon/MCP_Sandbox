# SQLServerClient

## When to use
Call this tool to explore and query a MySQL database. Use it for schema inspection, record counts, and SELECT queries.

## Input
- `sql` (string): a read-only SQL SELECT statement
- `schema_name` (string): schema/database to inspect
- `table_name` (string): specific table to inspect

## Output
Returns a formatted table, schema description, or record count depending on the operation.

## Allowed Operations
SELECT, INFORMATION_SCHEMA queries, schema inspection, row counts, read-only aggregations.

## Forbidden Operations
INSERT, UPDATE, DELETE, DROP, TRUNCATE, ALTER, CREATE, MERGE, EXEC, stored procedures, any DDL or DML.

## Schema Discovery Rules

- When listing tables, always filter to user schemas only:
  ```sql
  WHERE TABLE_SCHEMA NOT IN ('performance_schema', 'mysql', 'sys', 'information_schema')
  ```
- Never run COUNT(*) on system or metadata tables
- Inspect DISTINCT values of categorical columns before filtering on them

## Query Construction Rules

- Use explicit column names, avoid SELECT *
- Always use LIMIT on exploratory queries
- Filter early — push WHERE conditions as close to the table as possible
- GROUP BY primary key column + display name to avoid collisions
- Add ORDER BY only when the column is likely indexed

## MySQL-specific: prefer JOIN over EXISTS

MySQL does NOT optimize correlated EXISTS subqueries well on large tables.
EXISTS forces per-row subquery execution — on tables with 50M+ rows this causes timeouts.

**Preferred pattern for multi-table aggregation on MySQL:**
```sql
SELECT nb.primaryName, COUNT(DISTINCT tb.tconst) AS movie_credits
FROM imdb.name_basics nb
JOIN imdb.title_principals tp ON nb.nconst = tp.nconst
JOIN imdb.title_basics tb     ON tp.tconst = tb.tconst
WHERE tp.category IN ('actor', 'actress')
  AND tb.titleType = 'movie'
  AND tb.startYear > 1990
GROUP BY nb.nconst, nb.primaryName
ORDER BY movie_credits DESC
LIMIT 10;
```

**Avoid on MySQL:**
- Correlated EXISTS subqueries on tables > 10M rows
- EXISTS with multiple filter conditions inside the subquery

**COUNT(DISTINCT) is correct** when an actor can appear multiple times for the same title
(e.g. different roles) — DISTINCT removes duplicates before counting.

## Notes
- Treat database as production — minimize data volume
- Do not invent column names — always inspect schema first
- Do not claim success without tool confirmation
- Handle non-ASCII characters carefully, use UTF-8