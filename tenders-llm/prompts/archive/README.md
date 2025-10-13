# Prompt Archive

This directory contains all historical versions of the LLM classification prompt.

## Purpose

- Track evolution of the prompt over time
- Enable rollback to previous versions if needed
- Compare performance across versions
- Document what worked and what didn't

## Naming Convention

```
v{VERSION}_{DESCRIPTION}_{DATE}.md
```

Examples:
- `v1_classify_tender_conservative_2024-10-08.md`
- `v2_classify_tender_balanced_2024-10-08.md`
- `v3_classify_tender_with_negatives_2024-10-10.md`

## Current Versions

See `../PROMPT_CHANGELOG.md` for detailed history and performance metrics.

## How to Restore a Previous Version

```bash
# Copy archived version back to active prompts
cp prompts/archive/v1_classify_tender_conservative_2024-10-08.md prompts/classify_tender.md

# Update scripts to use the restored prompt
# Then test and commit
```

## Important

- Never delete archived prompts
- Always document why a version was deprecated
- Include performance metrics with each archive


