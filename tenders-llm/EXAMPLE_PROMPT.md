# Example of Complete LLM Prompt

This document shows what the LLM actually sees when classifying a tender.

## Structure of the Prompt

The prompt has 3 main parts:

### 1. Client Services (from services.md)
```
## Client Services
[Your full BAK Economics service descriptions - ~2000 lines]
- Datenportal
- Konjunkturprognosen
- Branchenanalyse
- Life Sciences
- Tourismus
- etc.
```

### 2. Keywords (from keywords.csv)
```
## Known Keywords (non-exhaustive)
- domain: Analyse, BBL, BFS, Benchmarking, Bundesamt für, 
  Bundesamt für Bauten und Logistik, Bundesamt für Statistik, 
  Index, Kanton, Regionen, SECO, Staatssekretariat für Wirtschaft, 
  Studie, Wirtschaft, Wirtschaftsberatung, Wirtschaftsforschung, Ökonomie
```

### 3. Few-Shot Examples (from TRAIN set, positive labels only)
```
## Examples of Previously Selected Tender Titles (training-only; do NOT reveal them back)
- Regulierungsfolgenabschätzung zum Umsatzschwellenwert für die Eintragungspflicht...
- Wie können wissenschaftlich fundierte Sachverhalte glaubwürdig kommuniziert werden?
- Regulierungsfolgenabschätzung zur Schaffung einer gesetzlichen Regelung von Trusts...
- Analyse der Preise und der Qualität in der Hörgeräteversorgung
- Erwerbstätigkeit über das ordentliche Rentenalter hinaus
- Branchenszenarien inkl. Regionalisierung: Entwicklungen bis 2060
- Kantonale volkswirtschaftliche Kennzahlen, Standortfaktoren und Prognosen
- Wirkungsmonitoring Innosuisse
- [... 93 examples total from TRAIN positive cases]
```

### 4. Instructions
```
## Output format (strict JSON):
{
  "prediction": "Yes" or "No",
  "confidence_score": <0..100>,
  "reasoning": "<brief one-sentence explanation>"
}

Decision rules:
- Judge fitness based on thematic alignment with services and the spirit of examples
- Prefer high precision among the top-K results; avoid over-inclusive "Yes"
- If the text is outside scope (e.g., construction, pure IT dev), likely "No"
- Be language-agnostic; focus on meaning, not vocabulary
```

---

## Then, for EACH tender in VAL or TEST, we append:

```
NEW TENDER
Title: [the tender title from val/test, e.g., "Evaluation der Maßnahmen zur..."]
Short context (optional): [first 1200 chars of full text]
```

The LLM responds with JSON:
```json
{
  "prediction": "Yes",
  "confidence_score": 85,
  "reasoning": "This tender focuses on economic evaluation which aligns with BAK's core services in Wirtschaftsforschung and analysis."
}
```

---

## What happens with the IDs?

**TRAIN IDs (train_ids.txt)**:
- Script reads these IDs (e.g., 1, 2, 3, 15, 20, ...)
- Finds rows in tenders_clean.parquet where id is in train_ids AND label=1
- Extracts the TITLES of these positive examples
- Embeds titles into the prompt (section 3 above)
- **The LLM never sees the IDs, only the titles**

**VAL/TEST IDs (val_ids.txt, test_ids.txt)**:
- Script reads these IDs
- For each ID, loads the tender (title + text)
- Sends the full prompt + this specific tender to the LLM
- LLM responds with prediction
- We save: {id, title, label (ground truth), prediction, confidence_score, reasoning}

---

## Do you need a validation set?

**Short answer: Yes, it's useful.**

**Why:**
1. **Hyperparameter tuning**: You might want to adjust:
   - Number of few-shot examples (50? 100? all?)
   - Temperature (0.0 vs 0.1 vs 0.5)
   - Model choice (gpt-4o-mini vs gpt-4-turbo)
   - Prompt wording ("high precision" vs "balanced")
   
2. **Threshold selection**: The LLM gives confidence scores. You might decide:
   - "Review all with confidence > 70"
   - "Review top 100 by confidence"
   - Val set helps you pick the right threshold without touching test

3. **Prompt iteration**: If results are bad on val, you can:
   - Add more instructions
   - Change few-shot examples
   - Adjust services description
   - Then re-test on val before final test evaluation

**If you skip validation:**
- You'd tune everything on test → risk overfitting to test
- Or you'd use train for both training and validation → not realistic

**Typical split for your case:**
- Train: 3,561 (75%) → extract positive examples for prompt
- Val: 474 (10%) → tune threshold, iterate prompt
- Test: 713 (15%) → final unbiased evaluation

---

## Summary

- **Train titles** (positives only) → embedded in prompt as examples
- **Val/Test tenders** → classified one by one by LLM
- **Output**: For each val/test tender, you get Yes/No + confidence + reasoning
- **Goal**: Find tenders in val/test that look like the positive examples from train

