"""
Phase 3: Build training dataset from existing pipeline runs.
Exports all drug-gene-abstract triples with LLM classifications
into a format ready for fine-tuning.
"""
import json
import os
import csv
import pandas as pd
from datetime import datetime

RESULTS_DIR = "results"
OUTPUT_DIR  = "data/annotations"
os.makedirs(OUTPUT_DIR, exist_ok=True)

# Gold standard labels from manual curation
# Format: (gene, drug) -> {"correct_class": ..., "correct_mechanism": ..., "correct_direction": ...}
GOLD_STANDARD = {
    # FSHR therapeutic candidates
    ("fshr", "follitropin delta"):           {"correct_class": "candidate_therapeutic_pair", "correct_mechanism": "inhibitor", "correct_direction": "decreases_activity"},
    ("fshr", "urofollitropin"):              {"correct_class": "candidate_therapeutic_pair", "correct_mechanism": "inhibitor", "correct_direction": "decreases_activity"},
    ("fshr", "follicle stimulating hormone"):{"correct_class": "candidate_therapeutic_pair", "correct_mechanism": "inhibitor", "correct_direction": "decreases_activity"},
    ("fshr", "follitropin"):                 {"correct_class": "candidate_therapeutic_pair", "correct_mechanism": "inhibitor", "correct_direction": "decreases_activity"},
    # FSHR safety
    ("fshr", "corifollitropin alfa"):        {"correct_class": "potential_safety_concern", "correct_mechanism": "activator", "correct_direction": "increases_activity"},
    ("fshr", "follitropin alfa"):            {"correct_class": "potential_safety_concern", "correct_mechanism": "activator", "correct_direction": "increases_activity"},
    ("fshr", "follitropin beta"):            {"correct_class": "potential_safety_concern", "correct_mechanism": "activator", "correct_direction": "increases_activity"},
    # PGR therapeutic candidates
    ("pgr", "drospirenone"):                 {"correct_class": "candidate_therapeutic_pair", "correct_mechanism": "agonist", "correct_direction": "increases_activity"},
    ("pgr", "ulipristal acetate"):           {"correct_class": "candidate_therapeutic_pair", "correct_mechanism": "agonist", "correct_direction": "increases_activity"},
    ("pgr", "dienogest"):                    {"correct_class": "candidate_therapeutic_pair", "correct_mechanism": "agonist", "correct_direction": "increases_activity"},
    ("pgr", "progesterone"):                 {"correct_class": "candidate_therapeutic_pair", "correct_mechanism": "agonist", "correct_direction": "increases_activity"},
    ("pgr", "medroxyprogesterone"):          {"correct_class": "candidate_therapeutic_pair", "correct_mechanism": "agonist", "correct_direction": "increases_activity"},
    ("pgr", "medroxyprogesterone acetate"):  {"correct_class": "candidate_therapeutic_pair", "correct_mechanism": "agonist", "correct_direction": "increases_activity"},
    ("pgr", "tamoxifen"):                    {"correct_class": "candidate_therapeutic_pair", "correct_mechanism": "agonist", "correct_direction": "increases_activity"},
    ("pgr", "danazol"):                      {"correct_class": "candidate_therapeutic_pair", "correct_mechanism": "agonist", "correct_direction": "increases_activity"},
    ("pgr", "mifepristone"):                 {"correct_class": "candidate_therapeutic_pair", "correct_mechanism": "agonist", "correct_direction": "increases_activity"},
    ("pgr", "estradiol"):                    {"correct_class": "candidate_therapeutic_pair", "correct_mechanism": "agonist", "correct_direction": "increases_activity"},
    # PGR safety
    ("pgr", "anastrozole"):                  {"correct_class": "potential_safety_concern", "correct_mechanism": "inhibitor", "correct_direction": "decreases_activity"},
    ("pgr", "fulvestrant"):                  {"correct_class": "potential_safety_concern", "correct_mechanism": "antagonist", "correct_direction": "decreases_activity"},
    ("pgr", "letrozole"):                    {"correct_class": "potential_safety_concern", "correct_mechanism": "inhibitor", "correct_direction": "decreases_activity"},
    ("pgr", "levonorgestrel"):               {"correct_class": "potential_safety_concern", "correct_mechanism": "inhibitor", "correct_direction": "decreases_activity"},
    ("pgr", "megestrol"):                    {"correct_class": "potential_safety_concern", "correct_mechanism": "inhibitor", "correct_direction": "decreases_activity"},
    ("pgr", "megestrol acetate"):            {"correct_class": "potential_safety_concern", "correct_mechanism": "inhibitor", "correct_direction": "decreases_activity"},
    ("pgr", "toremifene"):                   {"correct_class": "potential_safety_concern", "correct_mechanism": "inhibitor", "correct_direction": "decreases_activity"},
    # PTGER4 therapeutic
    ("ptger4", "adalimumab"):                {"correct_class": "candidate_therapeutic_pair", "correct_mechanism": "inhibitor", "correct_direction": "decreases_activity"},
    ("ptger4", "celecoxib"):                 {"correct_class": "candidate_therapeutic_pair", "correct_mechanism": "inhibitor", "correct_direction": "decreases_activity"},
    ("ptger4", "valproic acid"):             {"correct_class": "candidate_therapeutic_pair", "correct_mechanism": "inhibitor", "correct_direction": "decreases_activity"},
    # CDKN2A safety
    ("cdkn2a", "palbociclib"):               {"correct_class": "potential_safety_concern", "correct_mechanism": "activator", "correct_direction": "increases_activity"},
    # KDR safety
    ("kdr", "axitinib"):                     {"correct_class": "potential_safety_concern", "correct_mechanism": "inhibitor", "correct_direction": "decreases_activity"},
    ("kdr", "cabozantinib"):                 {"correct_class": "potential_safety_concern", "correct_mechanism": "inhibitor", "correct_direction": "decreases_activity"},
    ("kdr", "lenvatinib"):                   {"correct_class": "potential_safety_concern", "correct_mechanism": "inhibitor", "correct_direction": "decreases_activity"},
    ("kdr", "sorafenib"):                    {"correct_class": "potential_safety_concern", "correct_mechanism": "inhibitor", "correct_direction": "decreases_activity"},
    ("kdr", "sunitinib"):                    {"correct_class": "potential_safety_concern", "correct_mechanism": "inhibitor", "correct_direction": "decreases_activity"},
    ("kdr", "vandetanib"):                   {"correct_class": "potential_safety_concern", "correct_mechanism": "inhibitor", "correct_direction": "decreases_activity"},
    ("kdr", "tivozanib"):                    {"correct_class": "potential_safety_concern", "correct_mechanism": "inhibitor", "correct_direction": "decreases_activity"},
}

def load_evidence(json_path):
    """Load evidence JSON from a pipeline run."""
    if not os.path.exists(json_path):
        return []
    with open(json_path) as f:
        return json.load(f)

def build_dataset():
    rows = []
    json_files = [f for f in os.listdir(RESULTS_DIR) if f.endswith("_evidence.json")]

    print(f"Found {len(json_files)} evidence files to process...")

    for json_file in json_files:
        gene = json_file.split("_")[0].upper()
        json_path = os.path.join(RESULTS_DIR, json_file)
        pairs = load_evidence(json_path)

        for pair in pairs:
            drug = pair.get("drug", "").lower()
            gene_lower = gene.lower()
            gold = GOLD_STANDARD.get((gene_lower, drug), {})

            evidence_texts = pair.get("evidence_texts", [])
            evidence_classifications = pair.get("evidence_classifications", [])

            for i, et in enumerate(evidence_texts):
                abstract = et.get("abstract", "")
                title = et.get("title", "")
                pmid = et.get("pmid", "")

                if not abstract and not title:
                    continue

                text = (title or "") + ". " + (abstract or "")

                # Get LLM classification for this abstract
                ec = evidence_classifications[i] if i < len(evidence_classifications) else {}

                row = {
                    "gene":                     gene,
                    "drug":                     drug,
                    "pmid":                     pmid,
                    "text":                     text.strip()[:2000],
                    "source":                   et.get("source", "PubMed"),
                    # LLM labels
                    "llm_supports_relationship": ec.get("supports_drug_gene_relationship", ""),
                    "llm_directness":           ec.get("directness", ""),
                    "llm_mechanism":            ec.get("mechanism", ""),
                    "llm_direction":            ec.get("direction", ""),
                    "llm_biological_level":     ec.get("biological_level", ""),
                    "llm_evidence_type":        ec.get("evidence_type", ""),
                    "llm_species":              ec.get("species", ""),
                    "llm_evidence_strength":    ec.get("evidence_strength", ""),
                    "llm_confidence":           ec.get("confidence", ""),
                    "llm_rationale":            ec.get("rationale", ""),
                    # Gold standard labels (if available)
                    "gold_correct_class":       gold.get("correct_class", ""),
                    "gold_correct_mechanism":   gold.get("correct_mechanism", ""),
                    "gold_correct_direction":   gold.get("correct_direction", ""),
                    "is_gold_standard":         bool(gold),
                    "needs_manual_review":      bool(gold) and ec.get("mechanism", "") != gold.get("correct_mechanism", ""),
                }
                rows.append(row)

    df = pd.DataFrame(rows)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M")
    output_path = os.path.join(OUTPUT_DIR, f"training_dataset_{timestamp}.csv")
    df.to_csv(output_path, index=False)

    print(f"\n{'='*60}")
    print(f"TRAINING DATASET BUILT")
    print(f"{'='*60}")
    print(f"Total examples:        {len(df)}")
    print(f"Gold standard labeled: {df['is_gold_standard'].sum()}")
    print(f"Needs manual review:   {df['needs_manual_review'].sum()}")
    print(f"Unique genes:          {df['gene'].nunique()}")
    print(f"Unique drugs:          {df['drug'].nunique()}")
    print(f"Output:                {output_path}")

    # Also save gold standard subset separately
    gold_df = df[df["is_gold_standard"] == True]
    gold_path = os.path.join(OUTPUT_DIR, f"gold_standard_{timestamp}.csv")
    gold_df.to_csv(gold_path, index=False)
    print(f"Gold standard subset:  {gold_path} ({len(gold_df)} examples)")

    return df, output_path

if __name__ == "__main__":
    df, path = build_dataset()
    print(f"\nFirst few rows of gold standard examples:")
    gold = df[df["is_gold_standard"] == True][["gene","drug","llm_mechanism","gold_correct_mechanism","llm_direction","gold_correct_direction"]].head(10)
    print(gold.to_string(index=False))
