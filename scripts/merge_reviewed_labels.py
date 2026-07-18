import pandas as pd
import os
import glob

ANNOTATIONS_DIR = "data/annotations"

reviewed = pd.read_excel(
    os.path.join(ANNOTATIONS_DIR, "manual_review_152_reviewed.xlsx"),
    sheet_name="Reviewed Rows"
)
print(f"Loaded {len(reviewed)} reviewed rows")

training_files = sorted(glob.glob(os.path.join(ANNOTATIONS_DIR, "training_dataset_2*.csv")))
training_path  = training_files[-1]
training = pd.read_csv(training_path)
print(f"Loaded: {training_path} ({len(training)} rows)")

reviewed_subset = reviewed[[
    "gene", "drug", "pmid",
    "reviewed_gold_correct_mechanism",
    "reviewed_gold_correct_direction",
    "review_decision",
    "manual_label_confirmed"
]].copy()

reviewed_subset["pmid"] = reviewed_subset["pmid"].astype(str)
training["pmid"]        = training["pmid"].astype(str)

merged = training.merge(reviewed_subset, on=["gene","drug","pmid"], how="left")

mask = merged["reviewed_gold_correct_mechanism"].notna()
merged.loc[mask, "gold_correct_mechanism"] = merged.loc[mask, "reviewed_gold_correct_mechanism"]
merged.loc[mask, "gold_correct_direction"]  = merged.loc[mask, "reviewed_gold_correct_direction"]

print(f"Updated {mask.sum()} rows with reviewed labels")

output_path = os.path.join(ANNOTATIONS_DIR, "training_dataset_reviewed.csv")
merged.to_csv(output_path, index=False)
print(f"Saved: {output_path} ({len(merged)} rows)")
