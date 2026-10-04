# Clinical Flowsheet AI Mapping Copilot

AI-assisted healthcare metadata standardization using **Snowflake Cortex, Cortex Search, RAG, Python, SQL, and Streamlit** with a governed human-in-the-loop review workflow.

## Overview

Clinical systems often contain flowsheet metrics with inconsistent naming, domains, and terminology.

This project demonstrates how AI can help standardize clinical flowsheet metadata while keeping human review and deterministic validation in the workflow.

The pipeline uses Snowflake Cortex to generate candidate mappings, Cortex Search for semantic retrieval of trusted clinical metadata, and a Streamlit application for human review and approval.

## Architecture

```text
Raw Clinical Flowsheet Data
        |
        v
Extract Distinct Metrics
        |
        v
AI Candidate Generation
Snowflake Cortex / AI_COMPLETE
        |
        v
METRIC_CANDIDATES
        |
        v
Human Review
Streamlit Application
        |
        v
Approved Trusted Knowledge
METRIC_KNOWLEDGE
        |
        v
Cortex Search
Vector / Semantic Retrieval
        |
        v
RAG Mapping
        |
        v
Deterministic SQL Validation
        |
        v
Standardized Clinical Metrics