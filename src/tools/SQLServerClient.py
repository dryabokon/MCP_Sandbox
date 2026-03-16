from dotenv import load_dotenv
from pathlib import Path
import json
import os
import re
from typing import Optional
# ----------------------------------------------------------------------------------------------------------------------
from src.common.utils_query import SQLServerClient as SQLServerClientBackend
# ----------------------------------------------------------------------------------------------------------------------
_HERE = os.path.dirname(__file__)
description = open(os.path.join(_HERE, "../../.claude/tools/get_weather.md"),encoding="utf-8").read().strip()
# ----------------------------------------------------------------------------------------------------------------------
def get_definition():
    return {
        "name": os.path.basename(__file__).replace(".py", ""),
        "description": description,
        "input_schema": {
            "type": "object",
            "properties": {
                "action": {
                    "type": "string",
                    "enum": [
                        "list_tables",
                        "describe_table",
                        "query",
                        "full_structure",
                    ],
                    "description": "Operation to perform."
                },
                "schema_name": {
                    "type": "string",
                    "description": "SQL schema name, e.g. dbo"
                },
                "table_name": {
                    "type": "string",
                    "description": "SQL table name"
                },
                "sql": {
                    "type": "string",
                    "description": "Read-only SELECT query"
                }
            },
            "required": ["action"]
        }
    }


# ----------------------------------------------------------------------------------------------------------------------
def _is_safe_readonly_sql(sql: str) -> bool:
    if not sql or not sql.strip():
        return False

    sql_clean = sql.strip().lower()
    sql_clean = re.sub(r"\s+", " ", sql_clean)

    forbidden = [
        "insert ", "update ", "delete ", "drop ", "truncate ", "alter ",
        "create ", "merge ", "exec ", "execute ", "grant ", "revoke ",
        "deny ", "backup ", "restore ", "dbcc ", "use "
    ]
    if any(token in sql_clean for token in forbidden):
        return False

    allowed_starts = (
        "select ",
        "with ",
    )
    return sql_clean.startswith(allowed_starts)


# ----------------------------------------------------------------------------------------------------------------------
def _load_config():

    class Config:
        pass

    cfg = Config()
    root = Path(__file__).resolve().parents[2]
    if not os.path.isfile(root / ".env"):
        sql_connect = None
        print("[Error] .env file not found. Please create and provide DB_CONNECTION")
    else:
        load_dotenv(root / ".env")
        sql_connect = os.getenv("DB_CONNECTION")

    cfg.SQL_connect = sql_connect
    return cfg


# ----------------------------------------------------------------------------------------------------------------------
def run(
    action: str,
    schema_name: Optional[str] = None,
    table_name: Optional[str] = None,
    sql: Optional[str] = None,
) -> str:

    cfg = _load_config()
    client = SQLServerClientBackend(cfg)

    if action == "list_tables":
        df = client.get_tables(schema_name=schema_name)
        return client.prettify(df, showindex=False)

    if action == "describe_table":
        if not schema_name or not table_name:
            return "schema_name and table_name are required for describe_table"
        df = client.get_table_structure(schema_name=schema_name, table_name=table_name)
        return client.prettify(df, showindex=False)

    if action == "full_structure":
        df = client.get_full_structure()
        return client.prettify(df, showindex=False)

    if action == "query":
        if not sql:
            return "sql is required for query"
        if not _is_safe_readonly_sql(sql):
            return "Only read-only SELECT/WITH queries are allowed"
        try:
            df = client.execute_query(sql)
            return client.prettify(df, showindex=False)
        except Exception as e:
            return f"SQL ERROR"

    return f"Unsupported action: {action}"


# ----------------------------------------------------------------------------------------------------------------------
if __name__ == "__main__":
    print(json.dumps(get_definition(), indent=2))