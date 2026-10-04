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

cursor.execute("""
    SELECT
        M.NURSINGCHARTCELLTYPECAT,
        M.NURSINGCHARTCELLTYPEVALLABEL,
        M.NURSINGCHARTCELLTYPEVALNAME,
        M.RECORD_COUNT

    FROM CLINICAL_FLOWSHEET_AI.RAW.FLOWSHEET_MAPPING M

    WHERE M.MAPPING_STATUS = 'PENDING'

      AND NOT EXISTS (
          SELECT 1
          FROM CLINICAL_FLOWSHEET_AI.KNOWLEDGE.METRIC_CANDIDATES C
          WHERE C.SOURCE_CATEGORY = M.NURSINGCHARTCELLTYPECAT
            AND C.SOURCE_LABEL = M.NURSINGCHARTCELLTYPEVALLABEL
            AND C.SOURCE_METRIC = M.NURSINGCHARTCELLTYPEVALNAME
      )

    ORDER BY M.RECORD_COUNT DESC
    LIMIT 10
""")

metrics = cursor.fetchall()

print(f"Generating {len(metrics)} candidate mappings...\n")

for category, label, name, record_count in metrics:

    prompt = f"""
You are standardizing ICU clinical flowsheet metadata.

This is a candidate mapping only.

Return VALID JSON only with exactly these fields:
standard_domain,
standard_metric,
reason.

Use UPPERCASE_SNAKE_CASE for standard_domain and standard_metric.

Choose a concise clinical domain based on the meaning of the measurement.
Do not simply copy the source category.

Source category: {category}
Source label: {label}
Source metric: {name}
"""

    cursor.execute(
        """
        SELECT AI_COMPLETE(
            'openai-gpt-5-mini',
            %s
        )
        """,
        (prompt,)
    )

    response = cursor.fetchone()[0]

    try:
        # Clean the LLM response
        cleaned_response = response.strip()

        # Remove markdown code fences if the model returned them
        if cleaned_response.startswith("```"):
            cleaned_response = cleaned_response.replace("```json", "")
            cleaned_response = cleaned_response.replace("```", "")
            cleaned_response = cleaned_response.strip()

        result = json.loads(cleaned_response)

        # Sometimes the LLM returns JSON encoded inside another string
        if isinstance(result, str):
            result = json.loads(result)

        if not isinstance(result, dict):
            raise ValueError(f"Expected JSON object but received: {type(result)}")

        domain = result["standard_domain"]
        metric = result["standard_metric"]
        reason = result["reason"]

        cursor.execute(
            """
            INSERT INTO CLINICAL_FLOWSHEET_AI.KNOWLEDGE.METRIC_CANDIDATES
            (
                SOURCE_CATEGORY,
                SOURCE_LABEL,
                SOURCE_METRIC,
                PROPOSED_DOMAIN,
                PROPOSED_METRIC,
                AI_REASON,
                REVIEW_STATUS
            )
            VALUES (%s, %s, %s, %s, %s, %s, 'PENDING_REVIEW')
            """,
            (
                category,
                label,
                name,
                domain,
                metric,
                reason
            )
        )

        print(f"{name} -> {domain} / {metric}")

    except Exception as exc:
        print(f"FAILED: {name} - {exc}")

conn.commit()
cursor.close()
conn.close()

print("\nCandidate generation complete.")