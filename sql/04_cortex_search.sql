-- ============================================
-- Cortex Search service for RAG retrieval
-- ============================================

CREATE OR REPLACE CORTEX SEARCH SERVICE
CLINICAL_FLOWSHEET_AI.KNOWLEDGE.METRIC_SEARCH

ON SEARCH_TEXT

ATTRIBUTES STANDARD_DOMAIN, STANDARD_METRIC

WAREHOUSE = SNOWFLAKE_LEARNING_WH

TARGET_LAG = '1 day'

AUTO_SUSPEND = 1800

AS
SELECT
    SEARCH_TEXT,
    STANDARD_DOMAIN,
    STANDARD_METRIC,
    DEFINITION,
    KNOWN_ALIASES
FROM CLINICAL_FLOWSHEET_AI.KNOWLEDGE.METRIC_KNOWLEDGE;


-- ============================================
-- Test semantic retrieval
-- ============================================

SELECT
    VALUE:STANDARD_DOMAIN::STRING AS STANDARD_DOMAIN,
    VALUE:STANDARD_METRIC::STRING AS STANDARD_METRIC,
    VALUE:SEARCH_TEXT::STRING AS SEARCH_TEXT
FROM TABLE(
    FLATTEN(
        PARSE_JSON(
            SNOWFLAKE.CORTEX.SEARCH_PREVIEW(
                'CLINICAL_FLOWSHEET_AI.KNOWLEDGE.METRIC_SEARCH',
                '{
                    "query": "bedside glucose",
                    "columns": [
                        "STANDARD_DOMAIN",
                        "STANDARD_METRIC",
                        "SEARCH_TEXT"
                    ],
                    "limit": 3
                }'
            )
        ):results
    )
);