import os
import sys
# ---------------------------------------------------------------------------------------------------------------------
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../../"))
# ---------------------------------------------------------------------------------------------------------------------
from src.common.agent_runner import AgentRunner
from src.tools import SQLServerClient
# ---------------------------------------------------------------------------------------------------------------------
DEMOS = [
        (
            "1. Schema overview",
            """Use SQLServerClient action='list_tables' to list all tables with record counts.
            Summarize:
            - How many schemas and tables?
            - Which schema has the most tables?
            - Top 3 tables by record count.
            One paragraph + bullet list."""
        ),

        (
            "2. Complexity estimate",
            """Use SQLServerClient action='full_structure' to get all tables and columns.
            Estimate migration complexity:
            - Total column count across all tables
            - Flag tables with 30+ columns
            - Flag problematic types: text, ntext, image, xml, sql_variant, geography, geometry
            - Overall complexity: Low / Medium / High with reasoning."""
        ),

        (
            "3. Foreign key hotspots",
            """Use SQLServerClient action='query' with:

            SELECT
                fk.name AS fk_name,
                OBJECT_SCHEMA_NAME(fk.parent_object_id) AS from_schema,
                OBJECT_NAME(fk.parent_object_id) AS from_table,
                COL_NAME(fkc.parent_object_id, fkc.parent_column_id) AS from_col,
                OBJECT_SCHEMA_NAME(fk.referenced_object_id) AS to_schema,
                OBJECT_NAME(fk.referenced_object_id) AS to_table,
                COL_NAME(fkc.referenced_object_id, fkc.referenced_column_id) AS to_col
            FROM sys.foreign_keys fk
            JOIN sys.foreign_key_columns fkc ON fk.object_id = fkc.constraint_object_id
            ORDER BY from_schema, from_table

            Identify tables with most incoming FKs (highest blast radius if changed).
            Flag these as migration sequencing constraints."""
        ),

        (
            "4. Stored procedures & functions",
            """Use SQLServerClient action='query' with:

            SELECT
                OBJECT_SCHEMA_NAME(o.object_id) AS schema_name,
                o.name, o.type_desc,
                LEN(m.definition) AS code_length,
                o.modify_date
            FROM sys.objects o
            JOIN sys.sql_modules m ON o.object_id = m.object_id
            WHERE o.type IN ('P','FN','IF','TF')
            ORDER BY code_length DESC

            Summarize counts by type, top 5 by size, flag anything unmodified 2+ years."""
        ),

        (
            "5. Index landscape",
            """Use SQLServerClient action='query' with:

            SELECT
                OBJECT_SCHEMA_NAME(i.object_id) AS schema_name,
                OBJECT_NAME(i.object_id) AS table_name,
                i.name AS index_name,
                i.type_desc, i.is_unique, i.is_primary_key,
                COUNT(ic.column_id) AS col_count
            FROM sys.indexes i
            JOIN sys.index_columns ic ON i.object_id=ic.object_id AND i.index_id=ic.index_id
            WHERE i.type > 0
            GROUP BY i.object_id, i.name, i.type_desc, i.is_unique, i.is_primary_key
            ORDER BY col_count DESC

            Flag composite indexes with 4+ columns and note clustered vs non-clustered ratio."""
        ),

        (
            "6. Compare local DB vs MigVisor remote assessment",
            """First use SQLServerClient action='list_tables' to get local DB table count and schemas.
            Then use tl_asmt_query_db_summary from the MCP server to get the remote assessment summary.
            Compare:
            - Object counts: local vs what MigVisor has assessed
            - Are they the same database or different?
            - What does MigVisor know that raw SQL alone can't tell us?"""
        ),

        (
            "7. Deep dive on hardest object — both sources",
            """Step 1: Use SQLServerClient action='query' to find the largest stored procedure:
            SELECT TOP 1 OBJECT_SCHEMA_NAME(o.object_id) AS schema_name, o.name,
                   LEN(m.definition) AS code_length
            FROM sys.objects o JOIN sys.sql_modules m ON o.object_id=m.object_id
            WHERE o.type='P' ORDER BY code_length DESC

            Step 2: Use tl_anly_query_db or ag_anly_explain_complexity from MCP to get
            the complexity rating for that same object if it exists in the remote assessment.

            Step 3: Combine both views — raw size from SQL + MigVisor complexity score —
            into a single migration risk assessment for that object."""
        ),

        (
            "8. Full migration readiness report",
            """Generate a Migration Readiness Report using both SQLServerClient and MCP tools.

            ## 1. Scope
            Schemas, tables, views, procedures — from SQLServerClient.

            ## 2. Complexity Drivers
            Wide tables, FK hotspots, large procedures, problematic column types.

            ## 3. MigVisor Assessment Layer
            Use tl_asmt_query_db_summary + tl_anly_query_db for complexity tiers
            and top high-risk objects from the remote assessment.

            ## 4. Data Volume
            Top 3 tables by row count and migration time implications.

            ## 5. Migration Readiness
            Overall rating: Green / Amber / Red
            Three concrete action items for the migration team."""
        ),
    ]
# ---------------------------------------------------------------------------------------------------------------------
if __name__ == "__main__":

    query = DEMOS[1][1]

    RUNNER = AgentRunner(agent_name="agent_simple", prompt_path="../../.claude/agents/agent_migVisor.md", tools={"SQLServerClient": SQLServerClient})
    RUNNER.add_mcp_server("analytics-mcp", "sse" , "http://demo.migvisor.lab.epam.com:8080/sse")
    RUNNER.add_mcp_server("explainer-mcp", "http", "http://demo.migvisor.lab.epam.com:5173/mcp/explainer")

    query = sys.argv[1] if len(sys.argv) > 1 else query
    RUNNER.run(query)

