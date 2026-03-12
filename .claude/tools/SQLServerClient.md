## Tool Name

SQLServerClient

## Purpose

Provides safe, read-only access to a Microsoft SQL Server database for data exploration and analysis.

This tool allows agents to:

- Execute SELECT queries
- Inspect database schema
- List tables
- Retrieve table structure
- Format query results for readable display

## Capabilities

- Run read-only SQL queries
- List available tables
- Get table record counts
- Inspect table schema (columns and types)
- Retrieve full database structure
- Return results as formatted tables

## Allowed Operations

- SELECT
- Metadata queries (INFORMATION_SCHEMA)
- Schema inspection
- Row counts
- Read-only aggregation queries

## Forbidden Operations

- INSERT
- UPDATE
- DELETE
- DROP
- TRUNCATE
- ALTER
- CREATE
- MERGE
- EXEC / stored procedures
- Any data modification or administrative command

## Safety Model

- Assume production-like environment
- Minimize data volume retrieved
- Prefer limited queries (TOP, filters)
- Never execute destructive SQL
- Do not infer schema - inspect first
- Handle special characters and encoding properly
- Use UTF-8 encoding for all text operations
- Sanitize input to prevent encoding-related errors

## Inputs

Depending on wrapper tool implementation:

### Query Execution

- `sql` (string) read-only SQL SELECT statement (UTF-8 encoded)

### Schema Inspection

- `schema_name` (string) (UTF-8 encoded)
- `table_name` (string) (UTF-8 encoded)

## Outputs

- Formatted table text (UTF-8 encoded)
- Schema description
- Table list with sizes
- Record counts
- Structured database metadata
- All text output properly encoded to avoid character issues

## Usage Guidelines for Agents

- If user intent is unclear inspect schema first
- Prefer schema exploration before querying
- Avoid SELECT * for large tables
- Use TOP for exploratory queries
- Explain briefly what data is being retrieved
- Handle non-ASCII characters carefully
- Ensure proper encoding for column names and data values

## Typical Use Cases

- What tables exist in the database?
- Show structure of Customers table
- How many records are in Orders?
- Show top 10 recent transactions
- Summarize sales by month

## Output Format

- Human-readable table (UTF-8 encoded)
- Clean column headers
- Limited result size when exploring
- Clear indication when no data returned
- Properly escaped special characters

## Implementation

Backed by local Python utility:
`src/common/utils_query.py`

Wrapped for agent usage via:
`src/tools/sql_*.py`

All file operations use UTF-8 encoding to prevent encoding issues.