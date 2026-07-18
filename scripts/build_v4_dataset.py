"""
Build V4 training dataset from disagreements file.
Uses Claude labels as ground truth where Claude is confident.
"""
import pandas as pd
import os
import json

ANNOTATIONS_DIR = "data/annotations"

# Load disagreements
disagreements = pd.read_csv(os.path.join(ANNOTATIONS_DIR, "disagreements.csv"))
print(f"Total disagreements: {len(disagreements)}")

# Load training queue for full text
queue_path = os.path.join(ANNOTATIONS_DIR, "training_queue.jsonl")
queue_records = []
with open(queue_path) as f:
    for line in f:
        try:
            queue_records.append(json.loads(line))
        except:
            continue

print(f"Training queue records: {len(queue_records)}")

# Build lookup from queue: gene+drug+text snippet -> full record
queue_df = pd.DataFrame(queue_records)
print(f"Queue columns: {list(queue_df.columns)}")

# Filter disagreements where Claude is confident and specific
# i.e. Claude said something useful, not just unknown
SPECIFIC_MECHS = {
    "inhibitor", "antagonist", "agonist", "activator",
    "downregulator", "upregulator", "degrader", "binder_only"
}
SPECIFIC_DIRS = {
    "decreases_expression", "increases_expression",
    "decreases_activity", "increases_activity"
}

# High value disagreements: Claude specific, local model wrong
high_value = disagreements[
    (disagreements["claude_mech"].isin(SPECIFIC_MECHS)) |
    (disagreements["claude_dir"].isin(SPECIFIC_DIRS))
].copy()

print(f"\nHigh value disagreements (Claude specific): {len(high_value)}")
print(f"Claude mech distribution in high value:")
print(high_value["claude_mech"].value_counts().head(8))

# Build new training rows from high value disagreements
new_rows = []
for _, row in high_value.iterrows():
    new_rows.append({
        "gene":                    row.get("gene", ""),
        "drug":                    row.get("drug", ""),
        "pmid":                    "",
        "text":                    str(row.get("text", ""))[:2000],
        "source":                  "disagreement_claude_label",
        "llm_supports_relationship": row.get("claude_rel", False),
        "llm_directness":          "direct",
        "llm_mechanism":           row.get("claude_mech", "unknown"),
        "llm_direction":           row.get("claude_dir", "unclear"),
        "llm_biological_level":    "",
        "llm_evidence_type":       "",
        "llm_species":             "",
        "llm_evidence_strength":   "strong" if row.get("claude_conf", 0) > 0.7 else "moderate",
        "llm_confidence":          row.get("claude_conf", 0.8),
        "llm_rationale":           "Claude label from disagreement set",
        "gold_correct_class":      "",
        "gold_correct_mechanism":  row.get("claude_mech", "unknown"),
        "gold_correct_direction":  row.get("claude_dir", "unclear"),
        "is_gold_standard":        False,
        "needs_manual_review":     False,
        "reviewed_gold_correct_mechanism": row.get("claude_mech", "unknown"),
        "reviewed_gold_correct_direction": row.get("claude_dir", "unclear"),
        "review_decision":         "claude_label_from_disagreement",
        "manual_label_confirmed":  False,
    })

new_df = pd.DataFrame(new_rows)
print(f"\nNew training examples from disagreements: {len(new_df)}")

# Load existing V3 dataset
v3_path = os.path.join(ANNOTATIONS_DIR, "training_dataset_v3.csv")
v3 = pd.read_csv(v3_path)
print(f"Existing V3 dataset: {len(v3)} rows")

# Combine
combined = pd.concat([v3, new_df], ignore_index=True)
combined = combined.drop_duplicates(subset=["gene", "drug", "text"])

output_path = os.path.join(ANNOTATIONS_DIR, "training_dataset_v4.csv")
combined.to_csv(output_path, index=False)

print(f"\n{'='*50}")
print(f"V4 TRAINING DATASET")
print(f"{'='*50}")
print(f"V3 examples:          {len(v3)}")
print(f"New from disagreements: {len(new_df)}")
print(f"Combined total:       {len(combined)}")
print(f"Gold standard rows:   {int(combined['is_gold_standard'].sum())}")
print(f"Saved to:             {output_path}")
