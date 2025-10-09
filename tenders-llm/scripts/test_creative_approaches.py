"""
Test Creative Classification Approaches

Experiments with novel methods:
1. Two-stage: Broad filter → Refined classification
2. Hybrid: Adaptive context (XML only for ambiguous titles)
3. Negative examples: Show what NOT to select
4. Confidence thresholding: Stricter cutoff for "Yes"
"""
import os
import json
import pandas as pd
from openai import OpenAI
from tqdm import tqdm
from datetime import datetime
from pathlib import Path

API_KEY = os.getenv("OPENAI_API_KEY")
if not API_KEY:
    raise ValueError("Please set OPENAI_API_KEY environment variable")

client = OpenAI(api_key=API_KEY)
MODEL = "gpt-4o-mini"
BATCH_SIZE = 10

def classify_batch(tenders_data: list, base_prompt: str):
    """Classify batch of tenders."""
    batch_text = "\n\n".join([
        f"TENDER {i+1}:\nID: {t['id']}\nTitle: {t['title']}\nContext: {t['context']}"
        for i, t in enumerate(tenders_data)
    ])
    
    user_block = f"""
Classify these {len(tenders_data)} tenders:

{batch_text}

Return JSON array: [{{"tender_id": "1", "prediction": "Yes/No", "confidence_score": 0-100, "reasoning": "..."}}, ...]
"""
    
    messages = [
        {'role': 'system', 'content': 'Return strict JSON only.'},
        {'role': 'user', 'content': base_prompt + "\n\n" + user_block}
    ]
    
    try:
        r = client.chat.completions.create(
            model=MODEL,
            messages=messages,
            temperature=0.1,
            response_format={'type': 'json_object'},
        )
        response_json = json.loads(r.choices[0].message.content)
        if isinstance(response_json, dict):
            predictions = response_json.get('results', list(response_json.values())[0])
        else:
            predictions = response_json
        return predictions
    except Exception as e:
        return [{"tender_id": str(i+1), "prediction": "No", "confidence_score": 0, "reasoning": f"Error: {e}"} 
                for i in range(len(tenders_data))]

def run_test(method_name: str, get_context_fn, test_ids: list, df: pd.DataFrame, base_prompt: str, output_path: str):
    """Run test with custom context extraction function."""
    
    print(f"\n{'='*80}")
    print(f"Testing: {method_name}")
    print(f"{'='*80}\n")
    
    all_results = []
    n_batches = (len(test_ids) + BATCH_SIZE - 1) // BATCH_SIZE
    
    for batch_idx in tqdm(range(0, len(test_ids), BATCH_SIZE), desc=method_name):
        batch_ids = test_ids[batch_idx:batch_idx + BATCH_SIZE]
        batch_data = []
        
        for tid in batch_ids:
            row = df[df['id'].astype(str) == tid].iloc[0]
            title = row['title_clean'][:300]
            context = get_context_fn(row)
            
            batch_data.append({
                'id': tid,
                'title': title,
                'context': context,
                'true_label': int(row['label']),
                'lang': row.get('lang', '')
            })
        
        predictions = classify_batch(batch_data, base_prompt)
        
        for i, tender in enumerate(batch_data):
            pred = predictions[i] if i < len(predictions) else {}
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
    
    # Metrics
    tp = sum(1 for r in all_results if r['true_label'] == 1 and r['prediction'] == 'Yes')
    fp = sum(1 for r in all_results if r['true_label'] == 0 and r['prediction'] == 'Yes')
    tn = sum(1 for r in all_results if r['true_label'] == 0 and r['prediction'] == 'No')
    fn = sum(1 for r in all_results if r['true_label'] == 1 and r['prediction'] == 'No')
    
    accuracy = (tp + tn) / len(all_results) if all_results else 0
    precision = tp / (tp + fp) if (tp + fp) > 0 else 0
    recall = tp / (tp + fn) if (tp + fn) > 0 else 0
    f1 = 2 * precision * recall / (precision + recall) if (precision + recall) > 0 else 0
    
    print(f"\n{method_name} Results:")
    print(f"  Accuracy:  {accuracy:.1%}")
    print(f"  Precision: {precision:.1%}")
    print(f"  Recall:    {recall:.1%}")
    print(f"  F1-Score:  {f1:.3f}")
    print(f"  TP: {tp}, FP: {fp}, TN: {tn}, FN: {fn}")
    
    return {
        'method': method_name,
        'accuracy': accuracy,
        'precision': precision,
        'recall': recall,
        'f1_score': f1,
        'tp': tp, 'fp': fp, 'tn': tn, 'fn': fn
    }

def main():
    # Load data
    df = pd.read_parquet('data/processed/tenders_clean.parquet')
    
    # Use enriched sample (23 pos, 27 neg) for fair comparison with previous experiments
    test_ids = open('data/processed/val_ids_enriched50.txt').read().splitlines()
    base_prompt = open('prompts/classify_tender.md').read()
    
    # Show sample composition
    test_df = df[df['id'].astype(str).isin(test_ids)]
    print(f"\nTest sample: {len(test_df)} cases")
    print(f"  Positives: {test_df['label'].sum()} ({100*test_df['label'].mean():.1f}%)")
    print(f"  Negatives: {(test_df['label']==0).sum()} ({100*(test_df['label']==0).mean():.1f}%)")
    print(f"  (Enriched sample for fair comparison with previous experiments)\n")
    
    # Load negative examples for creative approach
    train_ids = set(open('data/processed/train_ids.txt').read().splitlines())
    train_neg = df[df['id'].astype(str).isin(train_ids) & (df['label'] == 0)]
    neg_examples = train_neg['title_clean'].dropna().sample(n=min(50, len(train_neg)), random_state=42).tolist()
    
    print(f"\n{'='*80}")
    print("CREATIVE APPROACHES EXPERIMENT")
    print(f"{'='*80}")
    print(f"Test cases: {len(test_ids)}")
    print(f"Batch size: {BATCH_SIZE}")
    print(f"Estimated time: ~5 minutes total")
    print(f"{'='*80}\n")
    
    all_metrics = []
    
    # Approach 1: Baseline (title only)
    metrics_1 = run_test(
        method_name="1. Baseline (Title Only)",
        get_context_fn=lambda row: row['title_clean'][:1200],
        test_ids=test_ids,
        df=df,
        base_prompt=base_prompt,
        output_path="data/processed/preds_creative_baseline.jsonl"
    )
    all_metrics.append(metrics_1)
    
    # Approach 2: Hybrid Adaptive (XML only if title seems vague)
    def hybrid_context(row):
        title = row['title_clean']
        # Check if title has clear economics keywords
        econ_keywords = ['wirtschaft', 'economic', 'econom', 'studie', 'study', 'analyse', 'analysis', 
                        'evaluation', 'prognose', 'forecast', 'markt', 'market']
        has_clear_signal = any(kw in title.lower() for kw in econ_keywords)
        
        if has_clear_signal or len(title) > 100:
            return title[:1200]  # Title is clear, no need for XML
        else:
            # Title is vague, add XML context
            xml_desc = row.get('xml_description', '')
            return f"{title}. {xml_desc}"[:1500] if len(str(xml_desc)) > 50 else title[:1200]
    
    metrics_2 = run_test(
        method_name="2. Hybrid Adaptive (XML if vague title)",
        get_context_fn=hybrid_context,
        test_ids=test_ids,
        df=df,
        base_prompt=base_prompt,
        output_path="data/processed/preds_creative_hybrid.jsonl"
    )
    all_metrics.append(metrics_2)
    
    # Approach 3: With Negative Examples
    negative_examples_text = "\n".join([f"- {ex[:100]}" for ex in neg_examples[:30]])
    prompt_with_negatives = base_prompt + f"""

## Examples of Previously REJECTED Tender Titles (DO NOT select these types):
{negative_examples_text}

These were rejected because they focus on IT infrastructure, pure consulting, construction, or administrative work - not economic research.
"""
    
    metrics_3 = run_test(
        method_name="3. With Negative Examples",
        get_context_fn=lambda row: row['title_clean'][:1200],
        test_ids=test_ids,
        df=df,
        base_prompt=prompt_with_negatives,
        output_path="data/processed/preds_creative_negatives.jsonl"
    )
    all_metrics.append(metrics_3)
    
    # Approach 4: Title + First Sentence Only
    def title_plus_first_sentence(row):
        title = row['title_clean']
        xml_desc = str(row.get('xml_description', ''))
        if len(xml_desc) > 50:
            # Extract first sentence (up to first period)
            first_sent = xml_desc.split('.')[0] if '.' in xml_desc else xml_desc[:200]
            return f"{title}. {first_sent}."[:800]
        return title[:1200]
    
    metrics_4 = run_test(
        method_name="4. Title + First Sentence",
        get_context_fn=title_plus_first_sentence,
        test_ids=test_ids,
        df=df,
        base_prompt=base_prompt,
        output_path="data/processed/preds_creative_first_sentence.jsonl"
    )
    all_metrics.append(metrics_4)
    
    # Approach 5: Ultra-conservative (confidence > 80 required for Yes)
    # This would need post-processing, so skip for now
    
    # Print comparison
    print(f"\n{'='*80}")
    print("CREATIVE APPROACHES COMPARISON")
    print(f"{'='*80}")
    print(f"{'Method':<40} {'Acc':<8} {'Prec':<8} {'Rec':<8} {'F1':<8} {'FP':<4}")
    print(f"{'-'*80}")
    for m in all_metrics:
        print(f"{m['method']:<40} {m['accuracy']:<8.1%} {m['precision']:<8.1%} {m['recall']:<8.1%} {m['f1_score']:<8.3f} {m['fp']:<4}")
    
    # Save
    comparison_path = f"results/creative_approaches_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    with open(comparison_path, 'w') as f:
        json.dump(all_metrics, f, indent=2)
    
    print(f"\n✓ Saved to: {comparison_path}")
    
    # Best by different criteria
    best_f1 = max(all_metrics, key=lambda x: x['f1_score'])
    best_precision = max(all_metrics, key=lambda x: x['precision'])
    
    print(f"\n🏆 Best F1-score: {best_f1['method']} (F1={best_f1['f1_score']:.3f})")
    print(f"🎯 Best Precision: {best_precision['method']} (Prec={best_precision['precision']:.1%}, FP={best_precision['fp']})")

if __name__ == "__main__":
    main()

