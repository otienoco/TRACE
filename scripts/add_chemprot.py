import os
import pandas as pd
from datasets import load_dataset

ANNOTATIONS = "data/annotations"

CHEMPROT_TO_MECHANISM = {
    "CPR:1":  "upregulator",
    "CPR:2":  "activator",
    "CPR:3":  "inhibitor",
    "CPR:4":  "antagonist",
    "CPR:5":  "agonist",
    "CPR:6":  "activator",
    "CPR:7":  "downregulator",
    "CPR:8":  "inhibitor",
    "CPR:9":  "modulator_unclear_direction",
    "CPR:10": "modulator_unclear_direction",
    "CPR:11": "binder_only",
    "CPR:12": "unknown",
    "CPR:13": "modulator_unclear_direction",
}

CHEMPROT_TO_DIRECTION = {
    "CPR:1":  "increases_expression",
    "CPR:2":  "increases_activity",
    "CPR:3":  "decreases_activity",
    "CPR:4":  "decreases_activity",
    "CPR:5":  "increases_activity",
    "CPR:6":  "increases_expression",
    "CPR:7":  "decreases_expression",
    "CPR:8":  "decreases_expression",
    "CPR:9":  "unclear",
    "CPR:10": "not_applicable",
    "CPR:11": "not_applicable",
    "CPR:12": "unclear",
    "CPR:13": "not_applicable",
}

POSITIVE_CPRS = {"CPR:1","CPR:2","CPR:3","CPR:4","CPR:5","CPR:6","CPR:7","CPR:8"}

def process_huggingface_chemprot():
    print("Loading ChemProt from HuggingFace...")
    dataset = load_dataset("bigbio/chemprot", trust_remote_code=True)
    rows = []

    for split_name in ["train", "validation", "test"]:
        split = dataset[split_name]
        print(f"Processing {split_name}: {len(split)} abstracts")

        for example in split:
            text = example.get("text", "")
            pmid = str(example.get("pmid", ""))
            if not text:
                continue

            # Entities is a dict of parallel lists
            ents     = example.get("entities", {})
            ent_ids  = ents.get("id", [])
            ent_types = ents.get("type", [])
            ent_texts = ents.get("text", [])

            # Build lookup: id -> {type, text}
            ent_lookup = {}
            for i, eid in enumerate(ent_ids):
                ent_lookup[eid] = {
                    "type": ent_types[i] if i < len(ent_types) else "",
                    "text": ent_texts[i] if i < len(ent_texts) else ""
                }

            # Relations is also a dict of parallel lists
            rels     = example.get("relations", {})
            rel_types = rels.get("type", [])
            rel_arg1  = rels.get("arg1", [])
            rel_arg2  = rels.get("arg2", [])

            for i, cpr in enumerate(rel_types):
                if cpr not in CHEMPROT_TO_MECHANISM:
                    continue

                arg1_id = rel_arg1[i] if i < len(rel_arg1) else ""
                arg2_id = rel_arg2[i] if i < len(rel_arg2) else ""

                chem = ent_lookup.get(arg1_id, {})
                gene = ent_lookup.get(arg2_id, {})

                # Chemical must be CHEMICAL type, gene must be GENE
                if "CHEMICAL" not in chem.get("type", ""):
                    continue
                if "GENE" not in gene.get("type", ""):
                    continue

                drug_name = chem.get("text", "").lower().strip()
                gene_name = gene.get("text", "").upper().strip()

                if not drug_name or not gene_name:
                    continue

                mechanism = CHEMPROT_TO_MECHANISM[cpr]
                direction = CHEMPROT_TO_DIRECTION[cpr]
                supports  = cpr in POSITIVE_CPRS

                rows.append({
                    "gene":                    gene_name,
                    "drug":                    drug_name,
                    "pmid":                    pmid,
                    "text":                    text[:2000],
                    "source":                  "ChemProt",
                    "llm_supports_relationship": supports,
                    "llm_directness":          "direct",
                    "llm_mechanism":           mechanism,
                    "llm_direction":           direction,
                    "llm_biological_level":    "protein_activity",
                    "llm_evidence_type":       "in_vitro",
                    "llm_species":             "human",
                    "llm_evidence_strength":   "strong" if supports else "insufficient",
                    "llm_confidence":          0.95 if supports else 0.1,
                    "llm_rationale":           f"ChemProt gold standard: {cpr}",
                    "gold_correct_class":      "candidate_therapeutic_pair" if supports else "",
                    "gold_correct_mechanism":  mechanism,
                    "gold_correct_direction":  direction,
                    "is_gold_standard":        True,
                    "needs_manual_review":     False,
                    "reviewed_gold_correct_mechanism": mechanism,
                    "reviewed_gold_correct_direction": direction,
                    "review_decision":         "chemprot_gold_standard",
                    "manual_label_confirmed":  True,
                })

    print(f"Extracted {len(rows)} ChemProt examples")
    return rows

def main():
    rows = process_huggingface_chemprot()
    if not rows:
        print("No rows extracted!")
        return

    existing = pd.read_csv(os.path.join(ANNOTATIONS, "training_dataset_reviewed.csv"))
    print(f"Existing training data: {len(existing)} rows")

    chemprot_df = pd.DataFrame(rows)
    combined    = pd.concat([existing, chemprot_df], ignore_index=True)
    combined    = combined.drop_duplicates(subset=["gene", "drug", "pmid"])

    output_path = os.path.join(ANNOTATIONS, "training_dataset_v3.csv")
    combined.to_csv(output_path, index=False)

    print(f"\n{'='*50}")
    print(f"V3 TRAINING DATASET")
    print(f"{'='*50}")
    print(f"Previous examples:  {len(existing)}")
    print(f"ChemProt examples:  {len(chemprot_df)}")
    print(f"Combined total:     {len(combined)}")
    print(f"Gold standard rows: {int(combined['is_gold_standard'].sum())}")
    print(f"Saved to:           {output_path}")

if __name__ == "__main__":
    main()
