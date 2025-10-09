"""
Create enriched validation sample similar to previous experiments.

Previous: 50 cases with 23 positives (46%)
This creates: 50 cases with ~20-25 positives for fair comparison.
"""
import pandas as pd
from pathlib import Path

# Load data
df = pd.read_parquet('data/processed/tenders_clean.parquet')
val_ids = set(open('data/processed/val_ids.txt').read().splitlines())
val_df = df[df['id'].astype(str).isin(val_ids)]

print(f"Full validation set: {len(val_df)} cases")
print(f"  Positives: {val_df['label'].sum()}")
print(f"  Negatives: {(val_df['label']==0).sum()}")

# Separate positives and negatives
val_pos = val_df[val_df['label'] == 1]
val_neg = val_df[val_df['label'] == 0]

# Create enriched sample: 23 positives + 27 negatives (like previous)
n_pos = min(23, len(val_pos))
n_neg = 50 - n_pos

pos_sample = val_pos.sample(n=n_pos, random_state=42)
neg_sample = val_neg.sample(n=n_neg, random_state=42)

enriched_sample = pd.concat([pos_sample, neg_sample])

print(f"\nEnriched sample created:")
print(f"  Total: {len(enriched_sample)} cases")
print(f"  Positives: {enriched_sample['label'].sum()} ({100*enriched_sample['label'].sum()/len(enriched_sample):.1f}%)")
print(f"  Negatives: {(enriched_sample['label']==0).sum()} ({100*(enriched_sample['label']==0).sum()/len(enriched_sample):.1f}%)")

# Save
output_path = 'data/processed/val_ids_enriched50.txt'
with open(output_path, 'w') as f:
    for vid in enriched_sample['id'].astype(str):
        f.write(f'{vid}\n')

print(f"\n✓ Saved to: {output_path}")
print(f"\nThis sample is similar to previous experiments for fair comparison!")

