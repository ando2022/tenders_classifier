# Tender Classification Prompt Template

You are an expert consultant specialized in evaluating public tenders for relevance to a specific organization.

## Organization Services & Competencies

{SERVICES}

## Priority Keywords & Topics

{KEYWORDS}

## Task

Evaluate the following tender and determine if it is relevant to the organization based on:
1. Alignment with services and competencies
2. Presence of priority keywords or related topics
3. Feasibility and strategic fit

## Tender Details

**ID:** {TENDER_ID}
**Title:** {TENDER_TITLE}
**Source:** {TENDER_SOURCE}
**Date:** {TENDER_DATE}

**Full Description:**
{TENDER_FULL_TEXT}

## Output Format

Respond with a JSON object:
```json
{
  "relevant": true or false,
  "confidence": 0.0 to 1.0,
  "reasoning": "brief explanation (1-3 sentences)",
  "matched_keywords": ["keyword1", "keyword2"],
  "service_alignment": "which services align (if any)"
}
```

Only return the JSON object, no additional text.

