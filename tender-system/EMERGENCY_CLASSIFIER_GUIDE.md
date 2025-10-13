# 🚨 Emergency Classifier Guide

**Emergency fallback system using cosine similarity when OpenAI is unavailable or to save costs.**

## 🎯 **Purpose**

The emergency classifier provides a cost-effective alternative to OpenAI classification by:
- **Matching new tenders** against known positive cases using cosine similarity
- **Automatically activating** when OpenAI fails or is unavailable
- **Learning from your database** of previously classified relevant tenders
- **Saving costs** by avoiding OpenAI API calls

---

## 🚀 **Quick Start**

### **1. Automatic Activation**
The emergency classifier automatically activates when:
- OpenAI API key is missing
- OpenAI service is down
- OpenAI rate limits are exceeded
- API costs need to be reduced

### **2. Manual Activation**
```bash
# Run scraper with emergency classifier only (no OpenAI)
python manage_emergency_classifier.py run --source simap --days-back 7
```

### **3. Load Positive Cases from Database**
```bash
# Load high-confidence relevant tenders from your database
python manage_emergency_classifier.py load-db --min-confidence 80
```

---

## 📊 **How It Works**

### **Similarity Matching Process**
1. **TF-IDF Vectorization**: Converts tender text to numerical vectors
2. **Cosine Similarity**: Compares new tenders against positive cases
3. **Threshold Matching**: Marks tenders as relevant if similarity ≥ threshold
4. **Confidence Scoring**: Converts similarity scores to confidence percentages

### **Model Training**
- **Positive Cases**: Known relevant tenders from your database
- **Text Processing**: Title + description combined
- **Feature Extraction**: TF-IDF with n-grams and stop word removal
- **Model Persistence**: Automatically saved and loaded

---

## 🛠️ **Management Commands**

### **Add Positive Cases**
```bash
# Add a single positive case
python manage_emergency_classifier.py add \
  --title "Economic Analysis of Regional Development" \
  --description "Comprehensive economic analysis of regional development patterns" \
  --confidence 0.95 \
  --source "manual"

# Add from database (recommended)
python manage_emergency_classifier.py load-db --min-confidence 80
```

### **Test Classification**
```bash
# Test with sample cases
python manage_emergency_classifier.py test

# Test with custom tender
python manage_emergency_classifier.py test \
  --title "Labor Market Research Project" \
  --description "Statistical analysis of employment trends"
```

### **Monitor Performance**
```bash
# Show statistics
python manage_emergency_classifier.py stats

# List all positive cases
python manage_emergency_classifier.py list
```

---

## ⚙️ **Configuration**

### **Similarity Threshold**
- **Default**: 0.3 (30% similarity)
- **Adjustable**: Modify `similarity_threshold` in `SimilarityClassifier`
- **Higher threshold**: More strict matching (fewer false positives)
- **Lower threshold**: More lenient matching (more false positives)

### **Model Parameters**
```python
# TF-IDF settings
max_features=5000,      # Maximum vocabulary size
stop_words='english',   # Remove common English words
ngram_range=(1, 2),     # Use single words and 2-word phrases
min_df=2,               # Word must appear in at least 2 documents
max_df=0.95             # Word must appear in less than 95% of documents
```

---

## 📈 **Performance Optimization**

### **Improve Accuracy**
1. **More Positive Cases**: Add more high-quality relevant tenders
2. **Quality over Quantity**: Focus on clear, unambiguous positive cases
3. **Regular Updates**: Add new positive cases as you classify more tenders
4. **Threshold Tuning**: Adjust similarity threshold based on results

### **Reduce False Positives**
```bash
# Increase threshold for stricter matching
# Edit similarity_threshold in SimilarityClassifier class
```

### **Reduce False Negatives**
```bash
# Decrease threshold for more lenient matching
# Edit similarity_threshold in SimilarityClassifier class
```

---

## 🔄 **Integration with Main System**

### **Automatic Fallback**
The main system automatically uses the emergency classifier when:
```python
try:
    # Try OpenAI classification first
    results = openai_classifier.classify_batch(tenders)
except Exception as e:
    # Automatic fallback to emergency classifier
    results = emergency_classifier.classify_batch(tenders)
```

### **Manual Override**
```python
from main import TenderOrchestrator

# Force emergency classifier only
orchestrator = TenderOrchestrator()
orchestrator.use_emergency_classifier_only(source='simap', days_back=7)
```

---

## 📊 **Output Format**

The emergency classifier returns the same format as OpenAI:
```python
{
    'is_relevant': True/False,
    'confidence_score': 0-100,
    'reasoning': 'Similarity explanation',
    'title_de': 'German title (fallback)',
    'summary': 'Generated summary',
    'similarity_score': 0.0-1.0,
    'best_match': 'Title of best matching case',
    'classification_method': 'cosine_similarity'
}
```

---

## 🎯 **Best Practices**

### **Building a Good Model**
1. **Start with Database**: Load existing high-confidence relevant tenders
2. **Add Manual Cases**: Include clear, unambiguous positive examples
3. **Regular Updates**: Continuously add new positive cases
4. **Monitor Performance**: Track accuracy and adjust threshold

### **Quality Positive Cases**
- **Clear Economic Focus**: Economic analysis, statistical studies, research
- **Specific Language**: Avoid generic terms, use domain-specific vocabulary
- **High Confidence**: Only include cases you're certain are relevant
- **Diverse Examples**: Cover different types of economic research

### **Testing Strategy**
```bash
# Test with known relevant tenders
python manage_emergency_classifier.py test --title "Economic Impact Study"

# Test with known irrelevant tenders
python manage_emergency_classifier.py test --title "IT Maintenance Contract"

# Monitor statistics regularly
python manage_emergency_classifier.py stats
```

---

## 🚨 **Emergency Scenarios**

### **OpenAI API Down**
```bash
# System automatically switches to emergency classifier
# No action needed - continues working normally
```

### **Rate Limit Exceeded**
```bash
# Emergency classifier takes over automatically
# Check logs for "Switching to emergency similarity classifier"
```

### **Cost Reduction**
```bash
# Force emergency classifier only
python manage_emergency_classifier.py run --source simap --days-back 7
```

### **No Internet Connection**
```bash
# Emergency classifier works offline
# Uses pre-trained model from disk
```

---

## 📁 **File Structure**

```
tender-system/
├── classifier/
│   ├── similarity_classifier.py      # Main emergency classifier
│   └── similarity_model.pkl          # Trained model (auto-generated)
├── manage_emergency_classifier.py    # CLI management tool
└── EMERGENCY_CLASSIFIER_GUIDE.md     # This guide
```

---

## 🔧 **Troubleshooting**

### **No Positive Cases Available**
```bash
# Load from database
python manage_emergency_classifier.py load-db

# Or add manually
python manage_emergency_classifier.py add --title "Economic Study" --description "Analysis"
```

### **Low Accuracy**
```bash
# Add more positive cases
python manage_emergency_classifier.py load-db --min-confidence 90

# Check current cases
python manage_emergency_classifier.py list
```

### **Model Not Loading**
```bash
# Rebuild model
python manage_emergency_classifier.py load-db
python manage_emergency_classifier.py test
```

### **High False Positive Rate**
```bash
# Increase similarity threshold in similarity_classifier.py
# Change similarity_threshold from 0.3 to 0.4 or higher
```

---

## 📊 **Monitoring & Metrics**

### **Key Metrics to Track**
- **Positive Cases Count**: More cases = better matching
- **Similarity Threshold**: Balance between precision and recall
- **Classification Method**: Track when emergency classifier is used
- **Confidence Scores**: Monitor similarity-based confidence

### **Log Messages**
```
✅ Used OpenAI classification
⚠️ OpenAI classification failed: [reason]
🔄 Switching to emergency similarity classifier...
✅ Used emergency similarity classification
📚 Loading positive cases from database...
```

---

## 🎉 **Benefits**

### **Cost Savings**
- **No API costs** for classification
- **Unlimited usage** without rate limits
- **Predictable costs** for tender processing

### **Reliability**
- **Always available** (no internet required after training)
- **Automatic fallback** when OpenAI fails
- **Consistent performance** based on your data

### **Customization**
- **Learns from your data** (not generic training)
- **Adjustable thresholds** for your specific needs
- **Continuous improvement** as you add more cases

---

## 🚀 **Getting Started Checklist**

- [ ] Install scikit-learn: `pip install scikit-learn>=1.3.0`
- [ ] Load positive cases from database: `python manage_emergency_classifier.py load-db`
- [ ] Test classification: `python manage_emergency_classifier.py test`
- [ ] Check statistics: `python manage_emergency_classifier.py stats`
- [ ] Run emergency-only scraper: `python manage_emergency_classifier.py run`
- [ ] Monitor logs for automatic fallback activation

**Your emergency classifier is now ready to provide reliable, cost-effective tender classification! 🎯**
