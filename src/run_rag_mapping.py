import os
from pathlib import Path

import snowflake.connector
from dotenv import load_dotenv

load_dotenv()

# Project SQL file
sql_file = (
    Path(__file__).resolve().parents[1]
    / "sql"
    / "05_rag_mapping.sql"
)

query = sql_file.read_text()

# Connect to Snowflake
conn = snowflake.connector.connect(
    account=os.getenv("SNOWFLAKE_ACCOUNT"),
    user=os.getenv("SNOWFLAKE_USER"),
    password=os.getenv("SNOWFLAKE_PASSWORD"),
    role=os.getenv("SNOWFLAKE_ROLE"),
    warehouse=os.getenv("SNOWFLAKE_WAREHOUSE"),
    database=os.getenv("SNOWFLAKE_DATABASE"),
    schema=os.getenv("SNOWFLAKE_SCHEMA")
)


cursor = conn.cursor()

try:
    cursor.execute("""
        SELECT
            CURRENT_USER(),
            CURRENT_ROLE(),
            CURRENT_WAREHOUSE(),
            CURRENT_DATABASE(),
            CURRENT_SCHEMA()
    """)

    print("Session:", cursor.fetchone())
    cursor.execute(query)

    columns = [column[0] for column in cursor.description]

    for row in cursor.fetchall():
        print(dict(zip(columns, row)))

finally:
    cursor.close()
    conn.close()