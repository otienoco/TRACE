"""
Rescore existing pipeline results with updated directionality classifier.
No need to rerun PubMed/Claude — just re-apply the classification logic.
"""
import os
import pandas as pd
import sys
sys.path.insert(0, 'src')
from gene_drug_repurposing.directionality.classify_direction import classify_therapeutic_direction

RESULTS_DIR = "results"

# Risk directions for MASLD genes
RISK_DIRECTIONS = {
    "ABCB11": "increased_gene_increases_risk",
    "ABCC2":  "increased_gene_increases_risk",
    "ALDH2":  "increased_gene_increases_risk",
    "APOE":   "decreased_gene_increases_risk",
    "CPN1":   "increased_gene_increases_risk",
    "FADS3":  "decreased_gene_increases_risk",
    "FLT1":   "increased_gene_increases_risk",
    "MYH7B":  "increased_gene_increases_risk",
    "PPARG":  "decreased_gene_increases_risk",
    "S1PR2":  "decreased_gene_increases_risk",
    "SCN2A":  "increased_gene_increases_risk",
    "VEGFA":  "increased_gene_increases_risk",
}

for gene, risk_direction in RISK_DIRECTIONS.items():
    csv_path = os.path.join(RESULTS_DIR, f"{gene}_MASLD_prioritized_drugs.csv")
    if not os.path.exists(csv_path):
        print(f"Missing: {csv_path}")
        continue

    df = pd.read_csv(csv_path)
    updated = 0
    for idx, row in df.iterrows():
        new_class, new_flag = classify_therapeutic_direction(
            risk_direction,
            str(row.get("mechanism", "unknown")),
            str(row.get("direction", "unclear"))
        )
        if new_class != row["therapeutic_class"]:
            updated += 1
        df.at[idx, "therapeutic_class"] = new_class
        df.at[idx, "manual_review_flag"] = new_flag

    df.to_csv(csv_path, index=False)
    print(f"{gene}: updated {updated} classifications")

print("\nDone! Run validate_masld.py to see new scores.")
