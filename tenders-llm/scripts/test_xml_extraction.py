"""
Test different XML extraction approaches on the same validation sample.
Based on test_prompt_versions.py but adapted for XML experiments.

Compares:
- Baseline (title only)
- XML description only
- XML description + deliverables
"""
import os
import json
import time
import sys
import pandas as pd
from openai import OpenAI
from tqdm import tqdm
from datetime import datetime
from pathlib import Path
from sklearn.model_selection import train_test_split

# Add utils to path
sys.path.append(str(Path(__file__).parent.parent))
from utils.xml_extractor import smart_extract

# Configuration
API_KEY = os.getenv("OPENAI_API_KEY")
if not API_KEY:
    raise ValueError("Please set OPENAI_API_KEY environment variable")

client = OpenAI(api_key=API_KEY)
MODEL = "gpt-4o-mini"
SLEEP_SEC = 1  # Very fast for testing (increase to 3-5 if errors, 22 for production)

def run_test(prompt_path, test_ids_path, output_path, extraction_method="title_only", version_name=""):
    """Run predictions on test set with given extraction method."""
    
    # Load data
    df = pd.read_parquet("data/processed/tenders_clean.parquet")
    test_ids = open(test_ids_path).read().splitlines()
    base_prompt = open(prompt_path, "r", encoding="utf-8").read()
    
    print(f"\n{'='*80}")
    print(f"Testing {version_name}")
    print(f"Extraction method: {extraction_method}")
    print(f"Test cases: {len(test_ids)}")
    print(f"Estimated time: ~{len(test_ids) * SLEEP_SEC / 60:.1f} minutes")
    print(f"{'='*80}\n")
    
    results = []
    errors = 0
    
    for tid in tqdm(test_ids, desc=f"{version_name}"):
        row = df[df['id'].astype(str) == tid].iloc[0]
        true_label = int(row['label'])
        
        # Build message based on extraction method
        title = row['title_clean'][:300]
        
        # Apply extraction method
        # Use PRE-EXTRACTED columns (from 00b_extract_xml_content.py)
        # This is MUCH faster than extracting on-the-fly!
        
        if extraction_method == "title_only":
            context = row['title_clean'][:1200]
        elif extraction_method == "xml_description":
            # Use pre-extracted description (Section 2.6)
            extracted = row.get('xml_description', '')
            context = extracted if len(str(extracted)) > 50 else row['title_clean'][:1200]
        elif extraction_method == "xml_desc_deliverables":
            # Use pre-extracted SIMAP sections (2.6 + 3.7 + 3.8)
            extracted = row.get('xml_simap_relevant', '')
            context = extracted if len(str(extracted)) > 50 else row['title_clean'][:1200]
        else:
            context = row['title_clean'][:1200]
        
        user_block = f"""
NEW TENDER
Title: {title}
Content: {context}
"""
        
        messages = [
            {'role': 'system', 'content': 'Follow the provided instructions and return strict JSON only.'},
            {'role': 'user', 'content': base_prompt + "\n\n" + user_block}
        ]
        
        try:
            r = client.chat.completions.create(
                model=MODEL,
                messages=messages,
                temperature=0.1,
                response_format={'type': 'json_object'},
            )
            
            pred = json.loads(r.choices[0].message.content)
            
            prediction = pred.get('prediction', 'No')
            confidence = pred.get('confidence_score', 0)
            reasoning = pred.get('reasoning', '')
            
            is_correct = (prediction == 'Yes' and true_label == 1) or (prediction == 'No' and true_label == 0)
            
            results.append({
                'id': tid,
                'title': row['title_clean'],
                'lang': row['lang'],
                'true_label': true_label,
                'prediction': prediction,
                'confidence_score': confidence,
                'reasoning': reasoning,
                'correct': is_correct
            })
            
        except Exception as e:
            errors += 1
            tqdm.write(f"Error on ID {tid}: {str(e)[:100]}")
            results.append({
                'id': tid,
                'title': row['title_clean'],
                'lang': row['lang'],
                'true_label': true_label,
                'prediction': 'No',
                'confidence_score': 0,
                'reasoning': f'Error: {str(e)[:100]}',
                'correct': False
            })
        
        time.sleep(SLEEP_SEC)
    
    # Save results
    with open(output_path, 'w', encoding='utf-8') as f:
        for rec in results:
            f.write(json.dumps(rec, ensure_ascii=False) + '\n')
    
    # Calculate metrics
    tp = sum(1 for r in results if r['true_label'] == 1 and r['prediction'] == 'Yes')
    fp = sum(1 for r in results if r['true_label'] == 0 and r['prediction'] == 'Yes')
    tn = sum(1 for r in results if r['true_label'] == 0 and r['prediction'] == 'No')
    fn = sum(1 for r in results if r['true_label'] == 1 and r['prediction'] == 'No')
    
    n_correct = sum(r['correct'] for r in results)
    accuracy = n_correct / len(results) if results else 0
    precision = tp / (tp + fp) if (tp + fp) > 0 else 0
    recall = tp / (tp + fn) if (tp + fn) > 0 else 0
    f1 = 2 * precision * recall / (precision + recall) if (precision + recall) > 0 else 0
    
    metrics = {
        'version': version_name,
        'extraction_method': extraction_method,
        'test_cases': len(results),
        'errors': errors,
        'accuracy': accuracy,
        'precision': precision,
        'recall': recall,
        'f1_score': f1,
        'tp': tp,
        'fp': fp,
        'tn': tn,
        'fn': fn,
        'timestamp': datetime.now().isoformat()
    }
    
    print(f"\n{version_name} Results:")
    print(f"  Accuracy:  {accuracy:.1%}")
    print(f"  Precision: {precision:.1%}")
    print(f"  Recall:    {recall:.1%}")
    print(f"  F1-Score:  {f1:.3f}")
    print(f"  TP: {tp}, FP: {fp}, TN: {tn}, FN: {fn}")
    print(f"\nSaved to: {output_path}")
    
    return metrics

def create_dev_sample(n_cases=50):
    """Create a stratified dev sample for testing."""
    from sklearn.model_selection import train_test_split
    
    df = pd.read_parquet("data/processed/tenders_clean.parquet")
    val_ids = set(open("data/processed/val_ids.txt").read().splitlines())
    val_df = df[df['id'].astype(str).isin(val_ids)]
    
    # Stratified sample
    dev_sample, _ = train_test_split(
        val_df, 
        train_size=n_cases,
        stratify=val_df['label'],
        random_state=42
    )
    
    # Save
    dev_path = Path("data/processed") / f"val_ids_test{n_cases}.txt"
    with open(dev_path, 'w') as f:
        for vid in dev_sample['id'].astype(str):
            f.write(f'{vid}\n')
    
    print(f"\nCreated test sample: {len(dev_sample)} cases, {dev_sample['label'].sum()} positives ({dev_sample['label'].mean():.1%})")
    print(f"Saved to: {dev_path}")
    
    return str(dev_path)

def main():
    # Create or use existing 50-case sample
    test_sample_path = "data/processed/val_ids_test50.txt"
    if not Path(test_sample_path).exists():
        print("Creating 50-case test sample...")
        test_sample_path = create_dev_sample(n_cases=50)
    else:
        print(f"Using existing test sample: {test_sample_path}")
    
    # Count test cases
    n_cases = len(open(test_sample_path).read().splitlines())
    n_methods = 3
    total_api_calls = n_cases * n_methods
    estimated_time_min = (total_api_calls * SLEEP_SEC) / 60
    
    print(f"\n{'='*80}")
    print(f"XML EXTRACTION EXPERIMENT")
    print(f"{'='*80}")
    print(f"Test cases: {n_cases}")
    print(f"Methods to test: {n_methods}")
    print(f"Total API calls: {total_api_calls}")
    print(f"Estimated time: ~{estimated_time_min:.0f} minutes (with {SLEEP_SEC}s sleep between calls)")
    print(f"Estimated cost: ~${total_api_calls * 0.02:.2f}")
    print(f"{'='*80}\n")
    
    all_metrics = []
    
    # Test 1: Baseline (title only)
    metrics_baseline = run_test(
        prompt_path="prompts/classify_tender.md",
        test_ids_path=test_sample_path,
        output_path="data/processed/preds_baseline_test50.jsonl",
        extraction_method="title_only",
        version_name="Baseline (Title Only)"
    )
    all_metrics.append(metrics_baseline)
    
    # Test 2: XML description only (Section 2.6)
    metrics_xml_desc = run_test(
        prompt_path="prompts/classify_tender.md",
        test_ids_path=test_sample_path,
        output_path="data/processed/preds_xml_desc_test50.jsonl",
        extraction_method="xml_description",
        version_name="XML Description (2.6)"
    )
    all_metrics.append(metrics_xml_desc)
    
    # Test 3: XML SIMAP sections (2.6 + 3.7 + 3.8)
    metrics_xml_simap = run_test(
        prompt_path="prompts/classify_tender.md",
        test_ids_path=test_sample_path,
        output_path="data/processed/preds_xml_simap_test50.jsonl",
        extraction_method="xml_desc_deliverables",
        version_name="XML SIMAP Sections (2.6+3.7+3.8)"
    )
    all_metrics.append(metrics_xml_simap)
    
    # Save comparison
    comparison_path = f"results/xml_extraction_comparison_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    os.makedirs("results", exist_ok=True)
    with open(comparison_path, 'w') as f:
        json.dump(all_metrics, f, indent=2)
    
    # Print comparison
    print(f"\n{'='*80}")
    print("XML EXTRACTION COMPARISON")
    print(f"{'='*80}")
    print(f"{'Method':<30} {'Accuracy':<12} {'Precision':<12} {'Recall':<12} {'F1':<10}")
    print(f"{'-'*80}")
    for m in all_metrics:
        print(f"{m['version']:<30} {m['accuracy']:<12.1%} {m['precision']:<12.1%} {m['recall']:<12.1%} {m['f1_score']:<10.3f}")
    
    print(f"\nFull comparison saved to: {comparison_path}")
    
    # Show best
    best = max(all_metrics, key=lambda x: x['f1_score'])
    print(f"\n🏆 Best approach: {best['version']} (F1={best['f1_score']:.3f})")

if __name__ == "__main__":
    main()

