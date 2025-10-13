# 📋 Client Output Guide

## What's Included in Client Reports

When tenders are processed through the system, the following information is automatically generated and can be exported for clients:

### ✅ Core Information (Always Included)

1. **Titel (Deutsch)** - German translation of tender title
   - Automatically translated from original language
   - If already in German, kept as-is

2. **Zusammenfassung** - AI-generated summary
   - 2-3 sentence concise overview
   - Highlights main objectives and key deliverables
   - Max 200 words for readability

3. **Volltext** - Full tender description/content
   - Complete tender text as provided by source
   - Can be optionally excluded for compact reports

4. **Veröffentlichungsdatum** - Publication date
   - Formatted as DD.MM.YYYY (German format)

5. **Einreichungsfrist** - Submission deadline
   - Formatted as DD.MM.YYYY (German format)
   - Shows when proposals must be submitted

6. **Relevanz (%)** - AI confidence score
   - 0-100% confidence that tender is relevant
   - Based on 92% accuracy classification model

7. **Begründung** - AI reasoning
   - Explains why tender was classified as relevant/not relevant

8. **Quelle** - Data source
   - SIMAP, Evergabe, etc.

9. **Auftraggeber** - Contracting authority
   - Organization issuing the tender

10. **Originaltitel** - Original title (if different from German)

---

## Export Formats

### 1. Excel Export (Recommended for Clients)

**Features:**
- Formatted columns with auto-width
- Proper German character encoding (ü, ä, ö, ß)
- Easy filtering and sorting
- Professional appearance

**Command:**
```bash
python export_client_report.py --relevant --format excel --min-confidence 70
```

**Output columns:**
- Titel (Deutsch)
- Zusammenfassung
- Veröffentlichungsdatum
- Einreichungsfrist
- Relevanz (%)
- Begründung
- Quelle
- Auftraggeber
- Originaltitel (if different)
- Volltext (optional)

### 2. CSV Export (For Further Processing)

**Command:**
```bash
python export_client_report.py --relevant --format csv --min-confidence 70
```

---

## Export Options

### Export Only Relevant Tenders

```bash
# High confidence only (≥75%)
python export_client_report.py --relevant --min-confidence 75

# Medium confidence (≥50%)
python export_client_report.py --relevant --min-confidence 50

# All relevant (≥0%)
python export_client_report.py --relevant --min-confidence 0
```

### Compact Export (Without Full Text)

```bash
# Smaller file, summary only
python export_client_report.py --relevant --no-fulltext
```

### Export All Tenders (Classified & Unclassified)

```bash
# All tenders
python export_client_report.py --all

# Last 7 days only
python export_client_report.py --all --days-back 7
```

### Custom Filename

```bash
python export_client_report.py --relevant --output "BAK_Relevant_Tenders_2025.xlsx"
```

---

## Using the Web UI for Export

### Via Streamlit Dashboard:

1. **Launch UI:**
   ```bash
   streamlit run ui/app.py
   ```

2. **Navigate to "✅ Relevant Tenders"**

3. **Set minimum confidence** using slider

4. **Click "📥 Export to Excel"** button

5. **File automatically created** with timestamp

The exported Excel file includes all client-ready information!

---

## Sample Export Output

### Excel Structure:

| Titel (Deutsch) | Zusammenfassung | Veröffentlichungsdatum | Einreichungsfrist | Relevanz (%) | Begründung | Quelle | Auftraggeber |
|-----------------|----------------|----------------------|-------------------|--------------|------------|---------|--------------|
| Wirtschaftliche Analyse des Arbeitsmarktes | Studie zur Analyse der Arbeitsmarktentwicklung in der Schweiz, inkl. Prognosen und Datenerhebung | 10.10.2025 | 30.11.2025 | 95% | Tender requires economic analysis and labor market research - core competency | SIMAP | Staatssekretariat für Wirtschaft |
| Evaluierung von Bildungsprogrammen | Wissenschaftliche Evaluation der Wirksamkeit von Berufsbildungsprogrammen mit Kosten-Nutzen-Analyse | 12.10.2025 | 15.12.2025 | 88% | Involves economic impact assessment and program evaluation | SIMAP | Bundesamt für Berufsbildung |

---

## API-Style Usage (Programmatic Export)

```python
from export_client_report import ClientReportExporter

# Create exporter
exporter = ClientReportExporter()

# Export relevant tenders
file = exporter.export_relevant_tenders(
    output_file="client_report.xlsx",
    min_confidence=70,
    format='excel',
    include_full_text=True
)

print(f"Report exported to: {file}")

# Check statistics
exporter.get_summary_stats()
```

---

## Understanding the Output Fields

### German Translation (Titel (Deutsch))
- **Why:** Makes Swiss German tenders accessible to all team members
- **How:** AI translates French/Italian/English titles to German
- **Quality:** High accuracy, preserves technical terms

### Summary (Zusammenfassung)
- **Why:** Quick overview without reading full text
- **What's included:** 
  - Main objective/purpose
  - Key deliverables
  - Specific requirements
- **Length:** 2-3 sentences, max 200 words
- **Use case:** Quick client briefings, executive summaries

### Dates
- **Publication Date:** When tender was published
- **Deadline:** Last date to submit proposal
- **Format:** DD.MM.YYYY (standard Swiss/German format)

### Relevance Score
- **Scale:** 0-100%
- **Meaning:**
  - 90-100%: Highly relevant, strong match
  - 75-89%: Relevant, good match
  - 50-74%: Possibly relevant, review needed
  - <50%: Less likely relevant
- **Basis:** 92% accuracy AI model

### AI Reasoning (Begründung)
- **Purpose:** Explains classification decision
- **Content:** Why tender was marked as relevant
- **Examples:**
  - "Requires economic forecasting and data analysis"
  - "Involves impact assessment - core competency"
  - "Survey-based research on employment trends"

---

## Best Practices for Client Reports

### 1. Filter by Confidence

For client presentations:
- **Use ≥75%** for high-quality, focused reports
- **Use ≥50%** for comprehensive review sessions

### 2. Include Context

Always export with:
- ✅ German titles (for accessibility)
- ✅ Summaries (for quick review)
- ✅ Deadlines (for planning)
- ✅ Full text (for detailed analysis)

### 3. Regular Updates

Export fresh reports:
- **Weekly:** After automated scraping runs
- **On-demand:** For urgent client requests
- **Monthly:** For comprehensive tender reviews

### 4. File Naming Convention

Recommended format:
```
BAK_Relevant_Tenders_YYYYMMDD.xlsx
BAK_All_Tenders_LastWeek_YYYYMMDD.xlsx
BAK_High_Confidence_Q4_2025.xlsx
```

---

## Advanced Export Queries

### Python Script for Custom Exports

```python
from database.models import get_session, Tender
import pandas as pd

session = get_session()

# Get tenders by specific criteria
tenders = session.query(Tender).filter(
    Tender.is_relevant == True,
    Tender.confidence_score >= 80,
    Tender.deadline >= datetime.now()  # Only upcoming deadlines
).all()

# Format for client
df = pd.DataFrame([{
    'Titel (DE)': t.title_de,
    'Zusammenfassung': t.summary,
    'Frist': t.deadline.strftime('%d.%m.%Y'),
    'Relevanz': f"{t.confidence_score:.0f}%",
    'Quelle': t.source.upper()
} for t in tenders])

# Export
df.to_excel('upcoming_high_confidence.xlsx', index=False)
```

---

## Frequently Asked Questions

### Q: Do I need the full text (Volltext)?

**A:** It depends:
- **For client review:** YES - clients may want full details
- **For quick overview:** NO - summary is sufficient
- **For archive:** YES - good to have complete information

### Q: How accurate are the German translations?

**A:** Very high accuracy:
- Technical terms preserved correctly
- Context-aware translation
- Reviewed by AI with domain knowledge
- Fallback: original if translation uncertain

### Q: Can I export to other formats?

**A:** Currently supported:
- ✅ Excel (.xlsx) - Recommended
- ✅ CSV (.csv) - For processing
- 🔄 PDF - Coming soon
- 🔄 Word (.docx) - Coming soon

### Q: What if a tender has no deadline?

**A:** Displays "N/A" or can be filtered out in post-processing

### Q: Can I customize the export columns?

**A:** Yes! Modify `export_client_report.py`:
```python
# Add custom field
row['Custom_Field'] = tender.some_field
```

---

## Example Workflow

### Weekly Client Report Workflow:

1. **Monday 9 AM:** Automated scraper runs
2. **Monday 10 AM:** Check dashboard for new relevant tenders
3. **Monday 11 AM:** Export high-confidence tenders (≥75%)
   ```bash
   python export_client_report.py --relevant --min-confidence 75 --output "Weekly_Report_$(date +%Y%m%d).xlsx"
   ```
4. **Monday 12 PM:** Review exported file
5. **Monday 2 PM:** Send to client/team

---

## Summary

✅ **What You Get:**
- German-translated titles
- AI-generated summaries
- Full tender text
- Publication & deadline dates
- Confidence scores & reasoning
- Source information

✅ **Export Formats:**
- Excel (client-ready)
- CSV (for processing)

✅ **How to Use:**
- CLI: `python export_client_report.py --relevant`
- UI: Click "Export to Excel" button
- API: Use `ClientReportExporter` class

✅ **Quality:**
- 92% classification accuracy
- Professional formatting
- German locale (dates, translations)
- Complete tender information

**Ready to create client reports! 🎯**

