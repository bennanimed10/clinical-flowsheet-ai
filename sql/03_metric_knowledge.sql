-- ============================================
-- Trusted clinical metric knowledge base
-- ============================================

CREATE OR REPLACE TABLE
CLINICAL_FLOWSHEET_AI.KNOWLEDGE.METRIC_KNOWLEDGE (
    STANDARD_DOMAIN VARCHAR,
    STANDARD_METRIC VARCHAR,
    DEFINITION VARCHAR,
    KNOWN_ALIASES VARCHAR,
    SEARCH_TEXT VARCHAR
);

INSERT INTO CLINICAL_FLOWSHEET_AI.KNOWLEDGE.METRIC_KNOWLEDGE
VALUES
(
    'VITAL_SIGN',
    'HEART_RATE',
    'Number of heart beats per minute.',
    'Heart Rate, HR, Pulse Rate',
    NULL
),
(
    'RESPIRATORY',
    'OXYGEN_SATURATION',
    'Peripheral oxygen saturation representing blood oxygenation, commonly measured as SpO2.',
    'O2 Saturation, Oxygen Saturation, SpO2',
    NULL
),
(
    'NEUROLOGICAL_ASSESSMENT',
    'GLASGOW_COMA_SCORE_TOTAL',
    'Total Glasgow Coma Scale score used to assess level of consciousness.',
    'GCS Total, Glasgow Coma Score Total',
    NULL
),
(
    'PAIN_ASSESSMENT',
    'PAIN_SCORE',
    'Numeric assessment of patient pain intensity.',
    'Pain Score, Pain Level, Pain Rating',
    NULL
),
(
    'GLUCOSE_MONITORING',
    'BLOOD_GLUCOSE_POINT_OF_CARE',
    'Blood glucose measurement performed at the bedside using point-of-care testing.',
    'Bedside Glucose, POC Glucose, Point of Care Glucose',
    NULL
);

UPDATE CLINICAL_FLOWSHEET_AI.KNOWLEDGE.METRIC_KNOWLEDGE
SET SEARCH_TEXT =
    'Domain: ' || STANDARD_DOMAIN ||
    ' | Metric: ' || STANDARD_METRIC ||
    ' | Definition: ' || DEFINITION ||
    ' | Known aliases: ' || KNOWN_ALIASES;