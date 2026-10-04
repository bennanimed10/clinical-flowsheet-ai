import json
import os

import snowflake.connector
from dotenv import load_dotenv

load_dotenv()

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

# For now, only process metrics that exist in our trusted knowledge base.
source_sql = """
SELECT
    M.NURSINGCHARTCELLTYPECAT,
    M.NURSINGCHARTCELLTYPEVALLABEL,
    M.NURSINGCHARTCELLTYPEVALNAME

FROM CLINICAL_FLOWSHEET_AI.RAW.FLOWSHEET_MAPPING M

JOIN CLINICAL_FLOWSHEET_AI.KNOWLEDGE.METRIC_CANDIDATES C
    ON M.NURSINGCHARTCELLTYPECAT = C.SOURCE_CATEGORY
   AND M.NURSINGCHARTCELLTYPEVALLABEL = C.SOURCE_LABEL
   AND M.NURSINGCHARTCELLTYPEVALNAME = C.SOURCE_METRIC

WHERE M.MAPPING_STATUS = 'PENDING'
  AND C.REVIEW_STATUS = 'APPROVED'
"""

cursor.execute(source_sql)
metrics = cursor.fetchall()

print(f"Processing {len(metrics)} metrics...\n")

for category, label, name in metrics:

    search_query = f"{category} {label} {name}"

    search_json = json.dumps({
        "query": search_query,
        "columns": [
            "STANDARD_DOMAIN",
            "STANDARD_METRIC",
            "SEARCH_TEXT"
        ],
        "limit": 3
    })

    rag_sql = f"""
    WITH RETRIEVED_KNOWLEDGE AS (

        SELECT
            INDEX AS RESULT_RANK,
            VALUE:SEARCH_TEXT::STRING AS SEARCH_TEXT

        FROM TABLE(
            FLATTEN(
                PARSE_JSON(
                    SNOWFLAKE.CORTEX.SEARCH_PREVIEW(
                        'CLINICAL_FLOWSHEET_AI.KNOWLEDGE.METRIC_SEARCH',
                        '{search_json}'
                    )
                ):results
            )
        )
    ),

    RAG_CONTEXT AS (

        SELECT
            LISTAGG(SEARCH_TEXT, ' || ')
            WITHIN GROUP (ORDER BY RESULT_RANK) AS CONTEXT

        FROM RETRIEVED_KNOWLEDGE
        WHERE RESULT_RANK < 3
    ),

    AI_RESULT AS (

        SELECT
            AI_COMPLETE(
                'openai-gpt-5-mini',

                CONCAT(
                    'You are standardizing ICU flowsheet metadata. ',
                    'Use ONLY the trusted clinical knowledge below. ',
                    'Do not invent a metric not present in the context. ',

                    'TRUSTED KNOWLEDGE: ',
                    CONTEXT,

                    ' SOURCE FLOWSHEET: ',
                    'Category: {category}. ',
                    'Label: {label}. ',
                    'Name: {name}. ',

                    'Return VALID JSON only with exactly these fields: ',
                    'standard_domain, standard_metric, reason.'
                )
            ) AS AI_RESPONSE

        FROM RAG_CONTEXT
    )

    SELECT
        TRY_PARSE_JSON(AI_RESPONSE):standard_domain::STRING,
        TRY_PARSE_JSON(AI_RESPONSE):standard_metric::STRING,
        TRY_PARSE_JSON(AI_RESPONSE):reason::STRING

    FROM AI_RESULT
    """

    cursor.execute(rag_sql)
    result = cursor.fetchone()

    if result and result[0] and result[1]:

        standard_domain, standard_metric, reason = result

        update_sql = """
        UPDATE CLINICAL_FLOWSHEET_AI.RAW.FLOWSHEET_MAPPING

        SET
            STANDARD_DOMAIN = %s,
            STANDARD_METRIC = %s,
            AI_REASON = %s,
            MAPPING_SOURCE = 'CORTEX_RAG',
            MAPPING_STATUS = 'PENDING_REVIEW'

        WHERE NURSINGCHARTCELLTYPECAT = %s
          AND NURSINGCHARTCELLTYPEVALLABEL = %s
          AND NURSINGCHARTCELLTYPEVALNAME = %s
        """

        cursor.execute(
            update_sql,
            (
                standard_domain,
                standard_metric,
                reason,
                category,
                label,
                name
            )
        )

        print(
            f"{name} -> "
            f"{standard_domain} / {standard_metric}"
        )

    else:
        print(f"FAILED: {name}")

conn.commit()

cursor.close()
conn.close()

print("\nBatch mapping complete.")