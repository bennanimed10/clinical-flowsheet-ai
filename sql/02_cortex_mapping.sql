-- ============================================
-- Cortex semantic interpretation
-- ============================================

WITH AI_RESULT AS (

    SELECT
        NURSINGCHARTCELLTYPECAT,
        NURSINGCHARTCELLTYPEVALLABEL,
        NURSINGCHARTCELLTYPEVALNAME,

        AI_COMPLETE(
            'openai-gpt-5-mini',

            CONCAT(
                'You are standardizing ICU clinical flowsheet metadata. ',

                'Return VALID JSON ONLY with exactly these fields: ',
                'standard_domain, standard_metric, reason. ',

                'standard_domain MUST be exactly one of: ',
                'VITAL_SIGN, ',
                'NEUROLOGICAL_ASSESSMENT, ',
                'PAIN_ASSESSMENT, ',
                'GLUCOSE_MONITORING, ',
                'RESPIRATORY, ',
                'HEMODYNAMIC, ',
                'SEDATION_ASSESSMENT, ',
                'OTHER. ',

                'Use UPPERCASE_SNAKE_CASE for standard_metric. ',
                'Do not simply copy the source category. ',
                'Classify according to the clinical meaning. ',

                'Source category: ', NURSINGCHARTCELLTYPECAT,
                '. Source label: ', NURSINGCHARTCELLTYPEVALLABEL,
                '. Source metric name: ', NURSINGCHARTCELLTYPEVALNAME
            )

        ) AS AI_RESPONSE

    FROM CLINICAL_FLOWSHEET_AI.RAW.FLOWSHEET_MAPPING
)

SELECT
    NURSINGCHARTCELLTYPECAT,
    NURSINGCHARTCELLTYPEVALLABEL,
    NURSINGCHARTCELLTYPEVALNAME,

    TRY_PARSE_JSON(AI_RESPONSE):standard_domain::STRING
        AS STANDARD_DOMAIN,

    TRY_PARSE_JSON(AI_RESPONSE):standard_metric::STRING
        AS STANDARD_METRIC,

    TRY_PARSE_JSON(AI_RESPONSE):reason::STRING
        AS AI_REASON

FROM AI_RESULT;