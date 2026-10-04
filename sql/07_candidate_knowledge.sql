-- ============================================
-- Candidate clinical knowledge
-- AI-generated proposals requiring review
-- ============================================

CREATE TABLE IF NOT EXISTS
CLINICAL_FLOWSHEET_AI.KNOWLEDGE.METRIC_CANDIDATES (

    SOURCE_CATEGORY VARCHAR,
    SOURCE_LABEL VARCHAR,
    SOURCE_METRIC VARCHAR,

    PROPOSED_DOMAIN VARCHAR,
    PROPOSED_METRIC VARCHAR,
    AI_REASON VARCHAR,

    REVIEW_STATUS VARCHAR DEFAULT 'PENDING_REVIEW'
);