# Tenders-LLM: Data Sources Analysis

**Generated:** October 9, 2025  
**Project:** bak-economics/tenders-llm

---

## Executive Summary

The `tenders-llm` project uses **multiple data sources** to build an LLM-based tender classification system. The primary data source is a collection of **4,748 Swiss public procurement tenders** extracted from SIMAP (Swiss public procurement platform), with 162 manually labeled as relevant to BAK Economics (3.4% positive rate).

---

## 1. Primary Data Sources

### 1.1 Main Tender Dataset

**Source File:** `data/raw/tenders_content.xlsx` (TITLES sheet)

**Origin:** SIMAP (Swiss Internet Platform for Public Procurement)
- Public procurement platform for Swiss government tenders
- Data extracted via SIMAP API/scraping
- Full-text content available in XML format

**Structure:**
```
Total Records: 4,748 tenders
Columns:
  - title           : Tender title (multilingual: DE/FR/IT)
  - deadline        : Submission deadline date
  - N2              : Binary label (0=not selected, 1=selected)
  - full text       : Full tender description (XML/HTML format)

Label Distribution:
  - Not Selected (0): 4,586 tenders (96.6%)
  - Selected (1):       162 tenders (3.4%)
```

**Content Sample:**
```
ID: 324265
Title: "(832) 810 Prestations TI dans le cadre du programme DaZu"
Deadline: 2008-10-30
Full Text: 10,000+ chars of XML-formatted tender details
Label: 0 (Not Selected)
```

**Data Quality:**
- Full text available for most tenders (stored as XML/HTML)
- Multilingual content (German, French, Italian)
- Date range: 2008-present
- Contains structured metadata: contracting authority, contract type, publication date

---

### 1.2 Alternative Tender Dataset

**Source File:** `data/raw/tenders.xlsx` (FULL SET sheet)

**Structure:**
```
Total Records: 4,748 tenders (same as tenders_content.xlsx)
Columns (9):
  - id              : Unique tender ID
  - projectid       : Project identifier
  - title           : Tender title
  - deadline        : Submission deadline
  - authName        : Contracting authority name
  - contType        : Contract type (e.g., SERVICES)
  - publicationDate : When tender was published
  - full-body text  : Full tender text (XML format)
  - N2              : Binary label (0/1)
```

**Note:** This appears to be an earlier version or alternative format of the same SIMAP data. The `tenders_content.xlsx` is currently used as the primary source.

---

### 1.3 Selected Tender IDs

**Source File:** `data/raw/selected_ids.csv`

**Purpose:** List of tender IDs that were manually selected as relevant by BAK Economics experts

**Structure:**
```
Format: One tender ID per line
Sample IDs: 1016039, 1017173, 1032287, 1043225...
Total: ~162 selected IDs (though file contains some 'nan' entries)
```

**Use Case:** Used to create binary labels (positive examples) for supervised learning

---

### 1.4 BAK Economics Services

**Source File:** `data/raw/Services.xlsx`

**Purpose:** Descriptions of services offered by BAK Economics (used for context in LLM prompts)

**Structure:**
```
Total Records: 37 services
Columns:
  - service name  : Name of service offering
  - description   : Detailed service description

Sample Services:
  1. "Datenportal" - Data portal services
  2. "Wirtschaft Schweiz - Konjunkturprognosen" - Swiss economic forecasts
  3. "Branchenanalyse" - Industry analysis
  ... 34 more services
```

**Use Case:** Injected into LLM prompt to provide context about what types of tenders BAK Economics should pursue

---

### 1.5 Case Study PDFs

**Source Location:** `data/raw/case_studies/`

**Content:** 222 PDF files containing past successful BAK Economics projects

**Purpose:** 
- Provide concrete examples of completed work
- Help LLM understand the type of research/analysis BAK Economics delivers
- Improve classification by showing what "success" looks like

**Processing:**
```
Extraction Script: scripts/00_extract_case_studies.py
Methods: 
  - pdfplumber (primary)
  - PyPDF2 (fallback)
Output: data/raw/case_studies_text.md (aggregated text)
```

**Status:** 222 PDFs available, extraction implemented but case study integration still experimental

---

## 2. Data Processing Pipeline

### 2.1 Data Reload Scripts

#### Script: `00_reload_data_with_fulltext.py` (CURRENT)

**Input:** `data/raw/tenders_content.xlsx` (TITLES sheet)

**Processing:**
1. Loads TITLES sheet with full text column
2. Cleans HTML/XML tags from full text
3. Creates sequential IDs (1 to N)
4. Uses title as fallback if full text missing
5. Parses deadline dates
6. Creates binary labels from N2 column

**Output:** `data/raw/tenders.csv`

**Key Cleaning:**
```python
- Remove XML/HTML tags: <tag> → ""
- Remove DOCTYPE declarations
- Decode HTML entities: &lt; → <, &amp; → &
- Remove excessive whitespace
- Filter: Only keep full text if > 100 chars
```

**Statistics Generated:**
```
Total tenders: 4,748
Selected (N2=1): 162 (3.4%)
With meaningful full text: ~X% (>100 chars)
Text length: mean, median, max, min per label
```

---

#### Script: `00_reload_data.py` (LEGACY)

**Input:** Google Drive file (hardcoded path)
```
/Users/anastasiiadobson/Library/CloudStorage/GoogleDrive-mybestdayistoday@gmail.com/
  .shortcut-targets-by-id/1Z7_7yHHWe-c-2QxwpkKB7i9KO3i9dwsR/
  BAK-Economics/Data/data_for_modelling/tenders.xlsx
```

**Processing:** Similar to current script but uses title only (no full text)

**Note:** Replaced by `00_reload_data_with_fulltext.py`

---

### 2.2 Data Preparation

#### Script: `01_prepare_data.py`

**Input:** `data/raw/tenders.csv`

**Processing:**
1. **Text Cleaning:** NFKC normalization, zero-width character removal
2. **Language Detection:** Auto-detect tender language (DE/FR/IT/EN)
3. **Label Creation:** Match IDs against `selected_ids.csv`
4. **Date Parsing:** Convert deadline strings to datetime

**Output:** `data/processed/tenders_clean.parquet`

**Text Cleaning Details:**
```python
from utils.text_clean import normalize_text
- NFKC Unicode normalization
- Remove/replace special characters
- Standardize whitespace
```

**Language Detection:**
```python
Using langdetect library
Input: First 1000 chars of title + full_text
Output: Language code (de, fr, it, en, unknown)
```

---

### 2.3 Train/Val/Test Splits

#### Script: `02_make_splits.py`

**Input:** `data/processed/tenders_clean.parquet`

**Splitting Strategy:**

**Option A: Time-based split** (if dates available)
```
Sort by deadline date
Train: 75% (earliest)
Val:   10%
Test:  15% (most recent)
```

**Option B: Stratified random split** (fallback)
```
Stratified by label (N2)
Train: 75%
Val:   10%  
Test:  15%
Random seed: 42
```

**Output Files:**
```
data/processed/train_ids.txt   (~3,561 IDs)
data/processed/val_ids.txt     (~475 IDs)
data/processed/test_ids.txt    (~712 IDs)
```

**Stratification:** Ensures positive rate (3.4%) is preserved across splits

---

### 2.4 Prompt Building

#### Script: `03_build_prompt.py`

**Data Sources Used:**

1. **Training Set Positives:**
   ```
   Source: tenders_clean.parquet + train_ids.txt
   Selection: All train set tenders where label=1
   Usage: Few-shot examples (max 100)
   Content: Title only (cleaned)
   ```

2. **BAK Services:**
   ```
   Source: data/raw/services.md (converted from Services.xlsx)
   Usage: Injected into prompt as context
   Fallback: "(No services file provided)"
   ```

3. **Keywords:**
   ```
   Source: data/raw/keywords.csv (OPTIONAL)
   Columns: keyword, lang, weight, category
   Usage: Grouped by category, injected into prompt
   Status: File not currently present
   Fallback: "(none provided)"
   ```

**Output:** `prompts/classify_tender.md`

**Prompt Structure:**
```markdown
1. System instruction (role definition)
2. Client Services section
3. Known Keywords section  
4. Few-shot examples (up to 100 positive tender titles)
5. Output format specification (JSON)
6. Decision rules
```

---

## 3. Data Flow Diagram

```
┌─────────────────────────────────────────────────────────────┐
│ EXTERNAL SOURCES                                            │
└─────────────────────────────────────────────────────────────┘
                              │
        ┌─────────────────────┼─────────────────────┐
        │                     │                     │
        ▼                     ▼                     ▼
  ┌──────────┐      ┌──────────────────┐   ┌──────────────┐
  │  SIMAP   │      │  Google Drive    │   │ Case Studies │
  │ Platform │      │  (Team Share)    │   │  (222 PDFs)  │
  └──────────┘      └──────────────────┘   └──────────────┘
        │                     │                     │
        │                     │                     │
        ▼                     ▼                     ▼
┌─────────────────────────────────────────────────────────────┐
│ RAW DATA (data/raw/)                                        │
├─────────────────────────────────────────────────────────────┤
│ • tenders_content.xlsx  (4,748 tenders, TITLES sheet)      │
│ • tenders.xlsx          (4,748 tenders, FULL SET sheet)    │
│ • selected_ids.csv      (162 positive IDs)                 │
│ • Services.xlsx         (37 service descriptions)          │
│ • case_studies/*.pdf    (222 PDF files)                    │
└─────────────────────────────────────────────────────────────┘
        │
        │ 00_reload_data_with_fulltext.py
        ▼
┌─────────────────────────────────────────────────────────────┐
│ INTERMEDIATE (data/raw/)                                    │
├─────────────────────────────────────────────────────────────┤
│ • tenders.csv           (cleaned, sequential IDs)          │
│ • selected_ids.csv      (used for labeling)                │
└─────────────────────────────────────────────────────────────┘
        │
        │ 01_prepare_data.py (clean text, detect lang, label)
        ▼
┌─────────────────────────────────────────────────────────────┐
│ PROCESSED (data/processed/)                                 │
├─────────────────────────────────────────────────────────────┤
│ • tenders_clean.parquet (normalized, labeled, with langs)  │
└─────────────────────────────────────────────────────────────┘
        │
        │ 02_make_splits.py (time-based or stratified)
        ▼
┌─────────────────────────────────────────────────────────────┐
│ SPLITS (data/processed/)                                    │
├─────────────────────────────────────────────────────────────┤
│ • train_ids.txt  (75%)                                     │
│ • val_ids.txt    (10%)                                     │
│ • test_ids.txt   (15%)                                     │
└─────────────────────────────────────────────────────────────┘
        │
        │ 03_build_prompt.py (inject services, examples)
        ▼
┌─────────────────────────────────────────────────────────────┐
│ PROMPTS (prompts/)                                          │
├─────────────────────────────────────────────────────────────┤
│ • classify_tender.md (with 100 few-shot examples)          │
└─────────────────────────────────────────────────────────────┘
        │
        │ 04_llm_predict.py (OpenAI API)
        ▼
┌─────────────────────────────────────────────────────────────┐
│ PREDICTIONS (data/processed/)                               │
├─────────────────────────────────────────────────────────────┤
│ • preds_val.jsonl                                          │
│ • preds_test.jsonl                                         │
│ • preds_all.jsonl                                          │
└─────────────────────────────────────────────────────────────┘
        │
        │ 05_eval.py (compute metrics)
        ▼
┌─────────────────────────────────────────────────────────────┐
│ RESULTS (reports/)                                          │
├─────────────────────────────────────────────────────────────┤
│ • pr_curve_val.png                                         │
│ • pr_curve_test.png                                        │
│ • metrics summary (console)                                │
└─────────────────────────────────────────────────────────────┘
```

---

## 4. Data Source Details

### 4.1 SIMAP Platform

**Official Name:** Swiss Internet Platform for Public Procurement

**URL:** simap.ch

**What it contains:**
- All Swiss federal, cantonal, and municipal public procurement tenders
- Multilingual tender descriptions (German, French, Italian, English)
- Structured metadata: deadlines, contract types, authorities
- Full tender documents (often as XML/HTML)

**Access Method:**
- Web scraping (likely method used)
- SIMAP API (OAuth flow documented in `archive/input/SIMAP_Quick_Guide_OAuthFlow.pdf`)
- Manual export to Excel

**Documentation Available:**
```
archive/input/
  - simap documentation.pdf
  - SIMAP_Quick_Guide_OAuthFlow.pdf
  - 2025-OJS184-00629187-en.pdf (sample tender)
```

---

### 4.2 Manual Labeling Process

**Who labeled:** BAK Economics domain experts

**Labeling criteria:** Tenders that:
- Match BAK Economics service offerings
- Require economic research/analysis expertise
- Are feasible given company resources
- Align with strategic priorities

**Label field:** `N2` column
```
0 = Not selected (not relevant)
1 = Selected (relevant to BAK Economics)
```

**Positive rate:** 3.4% (162 out of 4,748)
- Highly imbalanced dataset
- Typical for tender classification tasks

---

### 4.3 Missing/Optional Data Sources

**Keywords File:** `data/raw/keywords.csv`
- **Status:** Not currently present
- **Expected format:**
  ```csv
  keyword,lang,weight,category
  Wirtschaftsforschung,de,1.0,core
  Konjunkturprognose,de,0.9,forecasting
  étude économique,fr,1.0,core
  ```
- **Usage:** Would be injected into LLM prompt as thematic hints
- **Current workaround:** LLM relies on services + few-shot examples

**Services Markdown:** `data/raw/services.md`
- **Status:** Expected but not present (only Services.xlsx exists)
- **Conversion needed:** `Services.xlsx` → `services.md`
- **Current workaround:** Script has fallback for missing file

---

## 5. Data Quality & Characteristics

### 5.1 Text Length Distribution

**Full Text:**
```
Selected (N2=1):     Mean = ~878 chars
Not Selected (N2=0): Mean = ~7,215 chars
```

**Interpretation:**
- Selected tenders tend to have SHORTER titles/descriptions
- Negative examples contain more verbose contract details
- This suggests title alone may be sufficient signal

---

### 5.2 Multilingual Content

**Languages Detected:**
- German (de): Majority (~60-70%)
- French (fr): ~20-30%
- Italian (it): ~5-10%
- English (en): Rare (~1-2%)

**Challenge:**
- LLM must handle multilingual input
- Few-shot examples are mixed language
- Keywords would need multilingual variants

---

### 5.3 Date Range

**Earliest tender:** 2008
**Latest tender:** 2025 (likely)

**Implications:**
- Temporal drift in tender language/formats
- Time-based split may create distribution shift
- Older tenders may have different XML schemas

---

## 6. Experiment Findings (Data Impact)

### 6.1 Title vs Full Text (Experiment #3)

**Finding:** Full text does NOT improve performance

**Results:**
```
Title Only:  90% accuracy, 95% precision, 83% recall
Full Text:   88% accuracy, 91% precision, 83% recall
```

**Explanation:**
- Full text adds noise (legal boilerplate, XML artifacts)
- Selected tenders have shorter text (less signal)
- Title contains core semantic information

**Decision:** Use title-only approach (first 300 chars)

---

### 6.2 Few-Shot Examples (Experiment #2)

**Finding:** 93 positive examples significantly improve recall

**Impact:**
```
Conservative prompt (no examples): 0% recall
Balanced prompt (93 examples):     87% recall
```

**Implication:** Training set quality is critical
- 162 positive examples in total
- 93 used for few-shot (train split)
- Quality > quantity for few-shot learning

---

### 6.3 Case Studies (Experiment #4)

**Status:** Pending
**Hypothesis:** Case study examples may improve precision
**Data:** 222 PDFs extracted and ready
**Challenge:** Very long context (need summarization)

---

## 7. Data Provenance & Ownership

### 7.1 Source Systems

**SIMAP Data:**
- **Owner:** Swiss government (public data)
- **License:** Public domain (procurement transparency)
- **Updates:** Real-time (new tenders daily)

**Manual Labels (N2):**
- **Owner:** BAK Economics
- **Created by:** Domain experts (analysts)
- **Effort:** ~4,748 tender reviews
- **Value:** Proprietary training data

**Services Descriptions:**
- **Owner:** BAK Economics
- **Source:** Marketing materials, internal docs
- **Sensitivity:** Public-facing information

**Case Studies:**
- **Owner:** BAK Economics
- **Source:** Completed client projects
- **Sensitivity:** May contain confidential client info
- **Usage:** Anonymized for prompt engineering

---

### 7.2 Data Refresh Strategy

**Current State:** Static dataset (no refresh mechanism)

**Recommended Approach:**
```
1. Weekly SIMAP scrape → new tenders.xlsx
2. Run 00_reload → 01_prepare pipeline
3. Re-train/update prompt with new positives
4. Monitor prediction drift over time
```

**Monitoring Needed:**
- Track new tender language patterns
- Detect concept drift (e.g., COVID-related tenders)
- Update few-shot examples periodically

---

## 8. Summary: Key Data Assets

| Asset | Source | Records | Purpose | Status |
|-------|--------|---------|---------|--------|
| **Tenders** | SIMAP | 4,748 | Training/evaluation | ✅ Available |
| **Labels** | Manual | 162 pos | Supervised learning | ✅ Available |
| **Services** | BAK Econ | 37 | Prompt context | ✅ Available |
| **Case Studies** | Past projects | 222 PDFs | Few-shot examples | 🔄 Extracted |
| **Keywords** | Expert input | - | Prompt hints | ❌ Missing |
| **Live Feed** | SIMAP API | Continuous | Production | ❌ Not implemented |

---

## 9. Recommendations

### 9.1 Data Quality Improvements

1. **Create `keywords.csv`:**
   ```
   Extract key terms from:
   - Services.xlsx descriptions
   - Positive tender titles
   - BAK Economics website
   
   Organize by:
   - Language (de, fr, it)
   - Category (forecasting, analysis, surveys, etc.)
   - Weight (importance score)
   ```

2. **Convert Services.xlsx → services.md:**
   ```markdown
   # BAK Economics Services
   
   ## Economic Forecasting
   - Konjunkturprognosen
   - Description...
   
   ## Industry Analysis
   - Branchenanalyse
   - Description...
   ```

3. **Clean selected_ids.csv:**
   - Remove 'nan' entries (lines 19-163)
   - Verify all IDs exist in tenders dataset
   - Document selection criteria

### 9.2 Data Pipeline Enhancements

1. **Automate SIMAP Updates:**
   ```python
   # Implement in scripts/00_simap_fetch.py
   - Use SIMAP OAuth API
   - Fetch tenders from last N days
   - Append to existing dataset
   - Preserve manual labels
   ```

2. **Add Data Versioning:**
   ```
   data/
     raw/
       v1_2024-10-01/
         tenders_content.xlsx
       v2_2024-10-09/
         tenders_content.xlsx
     processed/
       v1_2024-10-01/
         tenders_clean.parquet
   ```

3. **Create Data Quality Checks:**
   ```python
   # Add to 01_prepare_data.py
   - Check for duplicate tender IDs
   - Validate N2 labels (only 0 or 1)
   - Flag missing full text
   - Detect language distribution shift
   ```

### 9.3 Documentation

1. **Create data/raw/README.md:**
   - Document each file's source
   - Explain update frequency
   - List field definitions

2. **Add data lineage:**
   - Track which raw file → processed file
   - Document transformations applied
   - Enable reproducibility

---

## 10. Appendix: File Inventory

### Complete File List

```
tenders-llm/
  data/
    raw/
      ├── tenders_content.xlsx       (4,748 rows, TITLES sheet)
      ├── tenders.xlsx               (4,748 rows, FULL SET sheet)
      ├── selected_ids.csv           (162 IDs + nans)
      ├── Services.xlsx              (37 services)
      ├── tenders.csv                (generated by 00_reload)
      └── case_studies/              (222 PDF files)
    
    processed/                        (generated)
      ├── tenders_clean.parquet      (cleaned + labeled)
      ├── train_ids.txt              (~3,561 IDs)
      ├── val_ids.txt                (~475 IDs)
      ├── test_ids.txt               (~712 IDs)
      ├── preds_val.jsonl            (validation predictions)
      ├── preds_test.jsonl           (test predictions)
      └── preds_all.jsonl            (all predictions)
  
  prompts/
    ├── classify_tender.md           (generated prompt)
    ├── classify_tender_balanced.md  (versioned prompt)
    └── archive/                     (old versions)
  
  scripts/
    ├── 00_reload_data_with_fulltext.py
    ├── 00_reload_data.py
    ├── 00_extract_case_studies.py
    ├── 01_prepare_data.py
    ├── 02_make_splits.py
    ├── 03_build_prompt.py
    ├── 04_llm_predict.py
    └── 05_eval.py
  
  utils/
    └── text_clean.py                (NFKC normalization)
  
  reports/
    ├── pr_curve_val.png
    ├── pr_curve_test.png
    └── (metrics in console output)
  
  results/
    └── prompt_comparison_*.json     (experiment comparisons)

archive/input/                       (documentation)
  ├── simap documentation.pdf
  ├── SIMAP_Quick_Guide_OAuthFlow.pdf
  ├── Smart tender tracking_keywords.docx
  └── Tender_monitoring.xlsx
```

---

**End of Analysis**

