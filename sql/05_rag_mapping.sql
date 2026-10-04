WITH RETRIEVED_KNOWLEDGE AS (

    SELECT
        INDEX AS RESULT_RANK,
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
                'Do not invent a metric that is not present in the context. ',

                'TRUSTED KNOWLEDGE: ',
                CONTEXT,

                ' SOURCE FLOWSHEET: ',
                'Category: Vital Signs and Infusions. ',
                'Label: Bedside Glucose. ',
                'Name: Bedside Glucose. ',

                'Return VALID JSON only with exactly these fields: ',
                'standard_domain, standard_metric, reason.'
            )
        ) AS AI_RESPONSE

    FROM RAG_CONTEXT
)

SELECT
    TRY_PARSE_JSON(AI_RESPONSE):standard_domain::STRING AS STANDARD_DOMAIN,
    TRY_PARSE_JSON(AI_RESPONSE):standard_metric::STRING AS STANDARD_METRIC,
    TRY_PARSE_JSON(AI_RESPONSE):reason::STRING AS AI_REASON

FROM AI_RESULT;