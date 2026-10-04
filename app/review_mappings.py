import os

import json

import pandas as pd
import snowflake.connector
import streamlit as st
from dotenv import load_dotenv

load_dotenv()

st.set_page_config(
    page_title="Clinical Flowsheet AI Mapping Copilot",
    layout="wide"
)


def get_connection():
    return snowflake.connector.connect(
        account=os.getenv("SNOWFLAKE_ACCOUNT"),
        user=os.getenv("SNOWFLAKE_USER"),
        password=os.getenv("SNOWFLAKE_PASSWORD"),
        role=os.getenv("SNOWFLAKE_ROLE"),
        warehouse=os.getenv("SNOWFLAKE_WAREHOUSE"),
        database=os.getenv("SNOWFLAKE_DATABASE"),
        schema=os.getenv("SNOWFLAKE_SCHEMA")
    )


st.title("Clinical Flowsheet AI Mapping Copilot")

status_filter = st.selectbox(
    "Review status",
    [
        "ALL",
        "PENDING_REVIEW",
        "APPROVED",
        "REJECTED"
    ]
)

conn = get_connection()

domain_cursor = conn.cursor()

domain_cursor.execute("""
    SELECT DISTINCT STANDARD_DOMAIN
    FROM CLINICAL_FLOWSHEET_AI.KNOWLEDGE.METRIC_KNOWLEDGE
    WHERE STANDARD_DOMAIN IS NOT NULL
    ORDER BY STANDARD_DOMAIN
""")

trusted_domains = [row[0] for row in domain_cursor.fetchall()]
domain_cursor.close()
if status_filter == "ALL":
    query = """
        SELECT
            SOURCE_CATEGORY,
            SOURCE_LABEL,
            SOURCE_METRIC,
            PROPOSED_DOMAIN,
            PROPOSED_METRIC,
            REVIEWED_DOMAIN,
            REVIEWED_METRIC,
            AI_REASON,
            REVIEW_STATUS
        FROM CLINICAL_FLOWSHEET_AI.KNOWLEDGE.METRIC_CANDIDATES
        ORDER BY SOURCE_METRIC
    """
else:
    query = """
        SELECT
            SOURCE_CATEGORY,
            SOURCE_LABEL,
            SOURCE_METRIC,
            PROPOSED_DOMAIN,
            PROPOSED_METRIC,
            REVIEWED_DOMAIN,
            REVIEWED_METRIC,
            AI_REASON,
            REVIEW_STATUS
        FROM CLINICAL_FLOWSHEET_AI.KNOWLEDGE.METRIC_CANDIDATES
        WHERE REVIEW_STATUS = %s
        ORDER BY SOURCE_METRIC
    """

if status_filter == "ALL":
    cursor = conn.cursor()
    cursor.execute(query)
else:
    cursor = conn.cursor()
    cursor.execute(query, (status_filter,))

rows = cursor.fetchall()

columns = [
    "SOURCE_CATEGORY",
    "SOURCE_LABEL",
    "SOURCE_METRIC",
    "PROPOSED_DOMAIN",
    "PROPOSED_METRIC",
    "REVIEWED_DOMAIN",
    "REVIEWED_METRIC",
    "AI_REASON",
    "REVIEW_STATUS"
]

df = pd.DataFrame(rows, columns=columns)

# Default the human-review values to the AI proposal.
# The original AI recommendation is still preserved separately.
if not df.empty:
    df["REVIEWED_DOMAIN"] = df["REVIEWED_DOMAIN"].fillna(
        df["PROPOSED_DOMAIN"]
    )

    df["REVIEWED_METRIC"] = df["REVIEWED_METRIC"].fillna(
        df["PROPOSED_METRIC"]
    )

# ------------------------------------------------
# Dashboard metrics
# ------------------------------------------------

count_cursor = conn.cursor()

count_cursor.execute("""
    SELECT
        REVIEW_STATUS,
        COUNT(*)
    FROM CLINICAL_FLOWSHEET_AI.KNOWLEDGE.METRIC_CANDIDATES
    GROUP BY REVIEW_STATUS
""")

status_counts = dict(count_cursor.fetchall())

col1, col2, col3 = st.columns(3)

col1.metric(
    "Pending Review",
    status_counts.get("PENDING_REVIEW", 0)
)

col2.metric(
    "Approved",
    status_counts.get("APPROVED", 0)
)

col3.metric(
    "Rejected",
    status_counts.get("REJECTED", 0)
)
if st.button("Generate Next 10 Candidates"):

    generate_cursor = conn.cursor()

    generate_cursor.execute("""
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

    metrics = generate_cursor.fetchall()

    if not metrics:
        st.info("No additional pending metrics found.")

    else:

        progress = st.progress(0)

        for i, (category, label, metric, record_count) in enumerate(metrics):

            prompt = f"""
You are standardizing ICU clinical flowsheet metadata.

Return VALID JSON only with exactly:
standard_domain,
standard_metric,
reason.

Use UPPERCASE_SNAKE_CASE.

This is only a candidate recommendation.
A human reviewer will approve, edit, or reject it.

Source category: {category}
Source label: {label}
Source metric: {metric}
"""

            generate_cursor.execute(
                """
                SELECT AI_COMPLETE(
                    'openai-gpt-5-mini',
                    %s
                )
                """,
                (prompt,)
            )

            response = generate_cursor.fetchone()[0]

            try:

                cleaned = response.strip()

                if cleaned.startswith("```"):
                    cleaned = cleaned.replace("```json", "")
                    cleaned = cleaned.replace("```", "")
                    cleaned = cleaned.strip()

                result = json.loads(cleaned)

                if isinstance(result, str):
                    result = json.loads(result)

                generate_cursor.execute(
                    """
                    INSERT INTO
                    CLINICAL_FLOWSHEET_AI.KNOWLEDGE.METRIC_CANDIDATES
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
                        metric,
                        result["standard_domain"],
                        result["standard_metric"],
                        result["reason"]
                    )
                )

            except Exception as exc:
                st.warning(f"Could not process {metric}: {exc}")

            progress.progress((i + 1) / len(metrics))

        conn.commit()

        st.success(
            f"{len(metrics)} new candidate mappings generated."
        )

        st.rerun()
        
st.divider()

st.subheader("Candidate Mappings")

if df.empty:

    st.info("No candidate mappings found for this status.")

else:

    edited_df = st.data_editor(
        df,
        use_container_width=True,
        hide_index=True,

        disabled=[
            "SOURCE_CATEGORY",
            "SOURCE_LABEL",
            "SOURCE_METRIC",
            "PROPOSED_DOMAIN",
            "PROPOSED_METRIC",
            "AI_REASON"
        ],

        column_config={

            "REVIEWED_DOMAIN": st.column_config.SelectboxColumn(
                "Reviewed Domain",
                options=trusted_domains,
                required=True
            ),

            "REVIEWED_METRIC": st.column_config.TextColumn(
                "Reviewed Metric",
                required=True
            ),

            "REVIEW_STATUS": st.column_config.SelectboxColumn(
                "Review Status",
                options=[
                    "PENDING_REVIEW",
                    "APPROVED",
                    "REJECTED"
                ],
                required=True
            )
        }
    )

    if st.button("Save Review Changes", type="primary"):

        update_cursor = conn.cursor()

        updated_count = 0

        for index, row in edited_df.iterrows():

            original = df.iloc[index]

            changed = (
                row["REVIEWED_DOMAIN"]
                != original["REVIEWED_DOMAIN"]
                or
                row["REVIEWED_METRIC"]
                != original["REVIEWED_METRIC"]
                or
                row["REVIEW_STATUS"]
                != original["REVIEW_STATUS"]
            )

            if changed:

                update_cursor.execute(
                    """
                    UPDATE
                    CLINICAL_FLOWSHEET_AI.KNOWLEDGE.METRIC_CANDIDATES

                    SET
                        REVIEWED_DOMAIN = %s,
                        REVIEWED_METRIC = %s,
                        REVIEW_STATUS = %s,
                        REVIEWED_AT = CURRENT_TIMESTAMP()

                    WHERE SOURCE_CATEGORY = %s
                    AND SOURCE_LABEL = %s
                    AND SOURCE_METRIC = %s
                    """,
                    (
                        row["REVIEWED_DOMAIN"],
                        row["REVIEWED_METRIC"],
                        row["REVIEW_STATUS"],
                        row["SOURCE_CATEGORY"],
                        row["SOURCE_LABEL"],
                        row["SOURCE_METRIC"]
                    )
                )

                updated_count += 1

        conn.commit()

        st.success(
            f"{updated_count} mapping(s) updated successfully."
        )

        st.rerun()

cursor.close()
count_cursor.close()
conn.close()
