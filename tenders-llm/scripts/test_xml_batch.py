"""
Fast XML Extraction Test with Batch Processing

Classifies multiple tenders in a single API call for 10-20x speedup.
"""
import os
import json
import pandas as pd
from openai import OpenAI
from tqdm import tqdm
from datetime import datetime
from pathlib import Path
from sklearn.model_selection import train_test_split

# Configuration
API_KEY = os.getenv("OPENAI_API_KEY")
if not API_KEY:
    raise ValueError("Please set OPENAI_API_KEY environment variable")

client = OpenAI(api_key=API_KEY)
MODEL = "gpt-4o-mini"
BATCH_SIZE = 10  # Classify 10 tenders per API call

def classify_batch(tenders_data: list, base_prompt: str):
    """Classify multiple tenders in one API call."""
    
    # Build batch request
    batch_text = "\n\n".join([
        f"TENDER {i+1}:\nID: {t['id']}\nTitle: {t['title']}\nContent: {t['context']}"
        for i, t in enumerate(tenders_data)
    ])
    
    user_block = f"""
You will classify {len(tenders_data)} tenders. For each, return a JSON object.

{batch_text}

Return a JSON array with {len(tenders_data)} objects, one for each tender:
[
  {{"tender_id": "1", "prediction": "Yes" or "No", "confidence_score": 0-100, "reasoning": "..."}},
  {{"tender_id": "2", "prediction": "Yes" or "No", "confidence_score": 0-100, "reasoning": "..."}},
  ...
]
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
        
        response_text = r.choices[0].message.content
        
        # Parse response
        response_json = json.loads(response_text)
        
        # Handle both {"results": [...]} and direct array
        if isinstance(response_json, dict) and 'results' in response_json:
            predictions = response_json['results']
        elif isinstance(response_json, list):
            predictions = response_json
        else:
            # Might be wrapped differently
            predictions = list(response_json.values())[0] if response_json else []
        
        return predictions
        
    except Exception as e:
        print(f"  Batch error: {str(e)[:100]}")
        # Return empty predictions on error
        return [{"tender_id": str(i+1), "prediction": "No", "confidence_score": 0, "reasoning": f"Error: {e}"} 
                for i in range(len(tenders_data))]

def run_batch_test(prompt_path, test_ids_path, output_path, extraction_method="title_only", version_name=""):
    """Run predictions with batching."""
    
    # Load data
    df = pd.read_parquet("data/processed/tenders_clean.parquet")
    test_ids = open(test_ids_path).read().splitlines()
    base_prompt = open(prompt_path, "r", encoding="utf-8").read()
    
    n_batches = (len(test_ids) + BATCH_SIZE - 1) // BATCH_SIZE
    
    print(f"\n{'='*80}")
    print(f"Testing {version_name}")
    print(f"Extraction method: {extraction_method}")
    print(f"Test cases: {len(test_ids)}")
    print(f"Batch size: {BATCH_SIZE}")
    print(f"Number of API calls: {n_batches} (vs {len(test_ids)} without batching)")
    print(f"Speedup: {len(test_ids)/n_batches:.1f}x faster")
    print(f"Estimated time: ~{n_batches * 5 / 60:.1f} minutes")
    print(f"{'='*80}\n")
    
    all_results = []
    
    # Process in batches
    for batch_idx in tqdm(range(0, len(test_ids), BATCH_SIZE), desc=f"{version_name}"):
        batch_ids = test_ids[batch_idx:batch_idx + BATCH_SIZE]
        batch_data = []
        
        for tid in batch_ids:
            row = df[df['id'].astype(str) == tid].iloc[0]
            title = row['title_clean'][:300]
            
            # Get context based on extraction method
            if extraction_method == "title_only":
                context = row['title_clean'][:1200]
            elif extraction_method == "xml_description":
                extracted = row.get('xml_description', '')
                context = extracted if len(str(extracted)) > 50 else row['title_clean'][:1200]
            elif extraction_method == "xml_desc_deliverables":
                extracted = row.get('xml_simap_relevant', '')
                context = extracted if len(str(extracted)) > 50 else row['title_clean'][:1200]
            else:
                context = row['title_clean'][:1200]
            
            batch_data.append({
                'id': tid,
                'title': title,
                'context': context,
                'true_label': int(row['label']),
                'lang': row.get('lang', '')
            })
        
        # Classify batch
        predictions = classify_batch(batch_data, base_prompt)
        
        # Match predictions to tenders
        for i, tender in enumerate(batch_data):
            # Find matching prediction (by tender_id or index)
            if i < len(predictions):
                pred = predictions[i]
            else:
                pred = {"prediction": "No", "confidence_score": 0, "reasoning": "No prediction returned"}
            
            result = {
                'id': tender['id'],
                'title': tender['title'],
                'lang': tender['lang'],
                'true_label': tender['true_label'],
                'prediction': pred.get('prediction', 'No'),
                'confidence_score': pred.get('confidence_score', 0),
                'reasoning': pred.get('reasoning', ''),
                'correct': (pred.get('prediction', 'No') == 'Yes' and tender['true_label'] == 1) or 
                          (pred.get('prediction', 'No') == 'No' and tender['true_label'] == 0)
            }
            all_results.append(result)
    
    # Save
    with open(output_path, 'w', encoding='utf-8') as f:
        for rec in all_results:
            f.write(json.dumps(rec, ensure_ascii=False) + '\n')
    
    # Calculate metrics
    tp = sum(1 for r in all_results if r['true_label'] == 1 and r['prediction'] == 'Yes')
    fp = sum(1 for r in all_results if r['true_label'] == 0 and r['prediction'] == 'Yes')
    tn = sum(1 for r in all_results if r['true_label'] == 0 and r['prediction'] == 'No')
    fn = sum(1 for r in all_results if r['true_label'] == 1 and r['prediction'] == 'No')
    
    n_correct = sum(r['correct'] for r in all_results)
    accuracy = n_correct / len(all_results) if all_results else 0
    precision = tp / (tp + fp) if (tp + fp) > 0 else 0
    recall = tp / (tp + fn) if (tp + fn) > 0 else 0
    f1 = 2 * precision * recall / (precision + recall) if (precision + recall) > 0 else 0
    
    print(f"\n{version_name} Results:")
    print(f"  Accuracy:  {accuracy:.1%}")
    print(f"  Precision: {precision:.1%}")
    print(f"  Recall:    {recall:.1%}")
    print(f"  F1-Score:  {f1:.3f}")
    print(f"  TP: {tp}, FP: {fp}, TN: {tn}, FN: {fn}")
    print(f"\nSaved to: {output_path}")
    
    return {
        'version': version_name,
        'extraction_method': extraction_method,
        'test_cases': len(all_results),
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

def main():
    # Use existing 50-case sample
    test_sample_path = "data/processed/val_ids_test50.txt"
    if not Path(test_sample_path).exists():
        print("Creating 50-case sample...")
        # Create it
        df = pd.read_parquet('data/processed/tenders_clean.parquet')
        val_ids = set(open('data/processed/val_ids.txt').read().splitlines())
        val_df = df[df['id'].astype(str).isin(val_ids)]
        sample, _ = train_test_split(val_df, train_size=50, stratify=val_df['label'], random_state=42)
        with open(test_sample_path, 'w') as f:
            for vid in sample['id'].astype(str):
                f.write(f'{vid}\n')
    
    n_cases = len(open(test_sample_path).read().splitlines())
    
    print(f"\n{'='*80}")
    print(f"FAST XML EXTRACTION TEST (BATCH MODE)")
    print(f"{'='*80}")
    print(f"Test cases: {n_cases}")
    print(f"Batch size: {BATCH_SIZE} tenders per API call")
    print(f"API calls needed: {(n_cases + BATCH_SIZE - 1) // BATCH_SIZE} per method")
    print(f"Methods to test: 3")
    print(f"Total API calls: {3 * ((n_cases + BATCH_SIZE - 1) // BATCH_SIZE)}")
    print(f"Estimated time: ~{3 * ((n_cases + BATCH_SIZE - 1) // BATCH_SIZE) * 5 / 60:.1f} minutes (vs {n_cases * 3 / 60:.0f} min without batching)")
    print(f"Speedup: ~{BATCH_SIZE}x faster!")
    print(f"{'='*80}\n")
    
    all_metrics = []
    
    # Test 1: Baseline
    metrics_baseline = run_batch_test(
        prompt_path="prompts/classify_tender.md",
        test_ids_path=test_sample_path,
        output_path="data/processed/preds_baseline_batch.jsonl",
        extraction_method="title_only",
        version_name="Baseline (Title Only)"
    )
    all_metrics.append(metrics_baseline)
    
    # Test 2: XML description
    metrics_xml_desc = run_batch_test(
        prompt_path="prompts/classify_tender.md",
        test_ids_path=test_sample_path,
        output_path="data/processed/preds_xml_desc_batch.jsonl",
        extraction_method="xml_description",
        version_name="XML Description (2.6)"
    )
    all_metrics.append(metrics_xml_desc)
    
    # Test 3: XML SIMAP sections
    metrics_xml_simap = run_batch_test(
        prompt_path="prompts/classify_tender.md",
        test_ids_path=test_sample_path,
        output_path="data/processed/preds_xml_simap_batch.jsonl",
        extraction_method="xml_desc_deliverables",
        version_name="XML SIMAP (2.6+3.7+3.8)"
    )
    all_metrics.append(metrics_xml_simap)
    
    # Save comparison
    comparison_path = f"results/xml_batch_comparison_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    os.makedirs("results", exist_ok=True)
    with open(comparison_path, 'w') as f:
        json.dump(all_metrics, f, indent=2)
    
    # Print comparison
    print(f"\n{'='*80}")
    print("BATCH XML EXTRACTION COMPARISON")
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

