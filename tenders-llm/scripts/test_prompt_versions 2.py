"""
Test different prompt versions on the same 50 validation cases.
Compares: v2 (title only) vs v3 (full text) vs v4 (full text + case studies)
"""
import os
import json
import time
import pandas as pd
from openai import OpenAI
from tqdm import tqdm
from datetime import datetime

# Configuration
API_KEY = os.getenv("OPENAI_API_KEY")
if not API_KEY:
    raise ValueError("Please set OPENAI_API_KEY environment variable")

client = OpenAI(api_key=API_KEY)
MODEL = "gpt-4o-mini"
SLEEP_SEC = 3

def run_test(prompt_path, test_ids_path, output_path, use_full_text=False, version_name=""):
    """Run predictions on test set with given prompt."""
    
    # Load data
    df = pd.read_parquet("data/processed/tenders_clean.parquet")
    test_ids = open(test_ids_path).read().splitlines()
    base_prompt = open(prompt_path, "r", encoding="utf-8").read()
    
    print(f"\n{'='*80}")
    print(f"Testing {version_name}")
    print(f"Prompt: {prompt_path}")
    print(f"Use full text: {use_full_text}")
    print(f"Test cases: {len(test_ids)}")
    print(f"{'='*80}\n")
    
    results = []
    errors = 0
    
    for tid in tqdm(test_ids, desc=f"{version_name}"):
        row = df[df['id'].astype(str) == tid].iloc[0]
        true_label = int(row['label'])
        
        # Build message - use full text if requested
        title = row['title_clean'][:300]
        if use_full_text and len(row.get('text_clean', '')) > 100:
            context = row['text_clean'][:4000]  # Use up to 4000 chars of full text
        else:
            context = row['title_clean'][:1200]  # Fallback to title
        
        user_block = f"""
NEW TENDER
Title: {title}
Full content: {context}
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
        'prompt_path': prompt_path,
        'use_full_text': use_full_text,
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

def main():
    test_ids_path = "data/processed/val_ids_test50_fulltext.txt"
    
    all_metrics = []
    
    # Test v2: Title only (baseline from before)
    metrics_v2 = run_test(
        prompt_path="prompts/classify_tender_balanced.md",
        test_ids_path=test_ids_path,
        output_path="data/processed/preds_v2_title_only.jsonl",
        use_full_text=False,
        version_name="v2 (Title Only)"
    )
    all_metrics.append(metrics_v2)
    
    # Test v3: Full text
    metrics_v3 = run_test(
        prompt_path="prompts/classify_tender_balanced.md",
        test_ids_path=test_ids_path,
        output_path="data/processed/preds_v3_full_text.jsonl",
        use_full_text=True,
        version_name="v3 (Full Text)"
    )
    all_metrics.append(metrics_v3)
    
    # Save comparison
    comparison_path = f"results/prompt_comparison_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    os.makedirs("results", exist_ok=True)
    with open(comparison_path, 'w') as f:
        json.dump(all_metrics, f, indent=2)
    
    print(f"\n{'='*80}")
    print("COMPARISON SUMMARY")
    print(f"{'='*80}")
    print(f"{'Version':<20} {'Accuracy':<12} {'Precision':<12} {'Recall':<12} {'F1':<10}")
    print(f"{'-'*80}")
    for m in all_metrics:
        print(f"{m['version']:<20} {m['accuracy']:<12.1%} {m['precision']:<12.1%} {m['recall']:<12.1%} {m['f1_score']:<10.3f}")
    
    print(f"\nFull comparison saved to: {comparison_path}")

if __name__ == "__main__":
    main()

