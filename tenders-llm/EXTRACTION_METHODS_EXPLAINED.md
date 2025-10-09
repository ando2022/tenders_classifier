# Extraction Methods: What Data Each Method Uses

## 📊 Data Flow Explanation

When you run `test_xml_extraction.py`, here's what data each method sends to the LLM:

---

## Method 1: Baseline (Title Only)

### Input Data
```
Title: {tender_title}  (first 300 chars)
Content: {tender_title}  (first 1200 chars, same as title)
```

### Example
```
Title: "Evaluation der Ausfuhrbeiträge Begleitmassnahmen"
Content: "Evaluation der Ausfuhrbeiträge Begleitmassnahmen"
```

**Total: ~150 chars sent to LLM**

### What the LLM Sees
- Just the tender title
- No additional context
- Fastest, cheapest

---

## Method 2: XML Description Only (Section 2.6)

### Input Data
```
Title: {tender_title}  (first 300 chars)
Content: {extracted_project_description}  (up to 1500 chars)
```

### Extraction Process
```python
# From raw XML (before tag removal)
full_text_raw = row['full_text_raw']  # Original XML with tags

# Extract these XML tags only:
extracted = extract_from_tags(full_text_raw, [
    'CONT.DESCR',  # Project description
    'CONT.NAME'    # Contract name
])

# Result: ~700-1500 chars of focused project description
```

### Example
```
Title: "Evaluation der Ausfuhrbeiträge Begleitmassnahmen"

Content: "Der Auftragnehmer führt eine vertiefte Regulierungsfolgenabschätzung 
(RFA) über die Änderung des Umsatzschwellenwertes für die Eintragungspflicht 
von Einzelunternehmen in das Handelsregister durch. Die Methodik richtet sich 
grundsätzlich nach den beim Bund gültigen Vorgaben für die RFA (vgl. Handbuch 
RFA und Checkliste RFA). Die Studie soll die zu erwartenden volkswirtschaftlichen 
Auswirkungen einer Erhöhung des Umsatzschwellenwertes aufzeigen..."
```

**Total: ~700-1500 chars sent to LLM**

### What the LLM Sees
- Tender title
- **+ Project description from section 2.6**
- More context about what the project actually is

---

## Method 3: XML Desc + Deliverables (Sections 2.6 + 3.7 + 3.8)

### Input Data
```
Title: {tender_title}  (first 300 chars)
Content: {extracted_simap_sections}  (up to 2000 chars)
```

### Extraction Process
```python
# Extract these SIMAP sections:
extracted = extract_from_tags(full_text_raw, [
    # Section 2.6: Gegenstand und Umfang des Auftrags
    'CONT.DESCR',  # Project description
    'CONT.NAME',   # Contract name
    'LOT.DESCR',   # Lot descriptions (deliverables)
    
    # Section 3.7: Eignungskriterien
    'OB01.COND.TECHNICAL',  # Technical/suitability criteria
    
    # Section 3.8: Geforderte Nachweise
    'OB01.COND.PROOF'  # Required evidence/qualifications
])

# Result: ~1000-2000 chars
```

### Example
```
Title: "Evaluation der Ausfuhrbeiträge Begleitmassnahmen"

Content: "Der Auftragnehmer führt eine vertiefte Regulierungsfolgenabschätzung 
(RFA) über die Änderung des Umsatzschwellenwertes... [project description]

LOT 1: Durchführung einer volkswirtschaftlichen Analyse der Auswirkungen...
[deliverables]

Fachliche Anforderungen: Fundierte Kenntnisse in Wirtschaftsforschung, 
Regulierungsfolgenabschätzung, volkswirtschaftliche Modellierung...
[suitability criteria]

Nachweise: Referenzen in ähnlichen Projekten, wissenschaftliche Publikationen 
im Bereich Wirtschaftspolitik...
[required evidence]"
```

**Total: ~1000-2000 chars sent to LLM**

### What the LLM Sees
- Tender title
- **+ Project description (2.6)**
- **+ What deliverables are expected (2.6)**
- **+ What expertise is required (3.7, 3.8)**

---

## 🔄 What Gets Excluded (All Methods)

### NOT Sent to LLM (Filtered Out)
```xml
<AUTH.CONTACT>
  Office fédéral, Bundesrain 20, 3003 Bern
  +41 31 322 39 11
  email@admin.ch
</AUTH.CONTACT>

<OB01.COND.PAYMENT>
  30 jours net après réception de la facture...
</OB01.COND.PAYMENT>

<OB01.INFO.LEGAL>
  Conformément à l'art. 30 LMP, la présente publication...
  [3000+ chars of legal boilerplate]
</OB01.INFO.LEGAL>

<OB01.COND.DOC>
  Documents can be downloaded from www.shab.ch...
</OB01.COND.DOC>
```

**Why excluded:**
- Addresses: Not relevant for classification
- Payment terms: Same for all tenders
- Legal boilerplate: Same for all tenders
- Document links: Administrative info

---

## 📊 Comparison: Data Volume

| Method | Input Size | What's Included | Cost Factor |
|--------|-----------|----------------|-------------|
| **Title Only** | ~150 chars | Title | 1x (baseline) |
| **XML Description** | ~700 chars | Title + project desc | 5x |
| **XML Relevant** | ~1,500 chars | Title + desc + deliverables + criteria | 10x |
| **Cleaned Full** | ~5,000 chars | Everything mixed together | 33x |
| **Raw XML** | ~17,000 chars | Everything + XML tags | 113x |

**Cost impact:**
- Title only: $0.20 per 20 cases
- XML description: $1.00 per 20 cases (5x more tokens)
- XML relevant: $2.00 per 20 cases (10x more tokens)

---

## 🎯 Your Test Results

### What Just Ran (With Balanced Prompt)

**Method 1: Title Only**
```
Input: "Evaluation der Ausfuhrbeiträge..."  (title)
LLM reasoning: Evaluates policy measures → economics research → Yes ✓
```

**Method 2: XML Description**
```
Input: "Evaluation der Ausfuhrbeiträge..." (title)
       + "Der Auftragnehmer führt eine RFA... volkswirtschaftlichen 
          Auswirkungen..." (description)
LLM reasoning: Policy evaluation study → economics research → Yes ✓
```

**Method 3: XML Desc+Deliverables**
```
Input: "Evaluation der Ausfuhrbeiträge..." (title)
       + "[project description]"
       + "[deliverables: economic analysis]"
       + "[criteria: economics expertise required]"
LLM reasoning: Economic policy study → matches services → Yes ✓
```

**All got it right!** But we don't know if extra context helped or was redundant.

---

## 💡 Why All Methods Got 100%

### Small Sample Issue

**The 20-case sample had:**
- 19 clear negatives (IT/software tenders) → Easy to reject
- 1 clear positive (economics evaluation) → Now caught by balanced prompt

**All methods could classify correctly because:**
- Title was enough for 19 negatives ("IT", "Software", "Submission")
- Title was enough for 1 positive ("Evaluation... Ausfuhrbeiträge")

### When XML Might Help

**Edge cases where title is vague:**
```
Title: "Consultant needed" (vague)
Description: "...wirtschaftliche Analyse... Konjunkturprognosen..." (clearly economics)
→ XML extraction helps!

vs

Title: "Wirtschaftliche Studie Tourismus" (clear)
Description: "..." (doesn't matter, title was enough)
→ XML extraction redundant
```

---

## 🔍 To Know If XML Actually Helps

### Need Larger Sample

Test on **50-100 cases** to include:
- More positives (2-5 instead of 1)
- More edge cases (vague titles)
- Statistical significance

### Current Conclusion

**On this 20-case sample:**
- XML extraction works (verified)
- But title alone was sufficient
- All methods: 100% accuracy

**Need more data to know if XML provides real benefit!**

---

## 📋 Summary: What Data Each Method Uses

| Method | Data Source | Sections | Typical Size |
|--------|------------|----------|--------------|
| **Baseline** | title_clean | Title only | 150 chars |
| **XML Desc** | full_text_raw → extract | 2.6 (CONT.DESCR) | 700 chars |
| **XML Relevant** | full_text_raw → extract | 2.6 + 3.7 + 3.8 | 1,500 chars |

**All use the balanced prompt** which includes:
- ✅ 37 BAK services descriptions
- ✅ Keywords list
- ✅ ~100 positive tender examples from training set
- ✅ Balanced decision rules (not conservative)

---

**Bottom line: XML extraction is working and extracting the right SIMAP sections, but on this small sample, title alone was sufficient!** 🎯

