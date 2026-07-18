import argparse, sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))
from gene_drug_repurposing.pipeline import run_pipeline

parser = argparse.ArgumentParser(description="Gene-to-Drug Repurposing Pipeline")
parser.add_argument("--gene", required=True)
parser.add_argument("--disease", default=None)
parser.add_argument("--risk_direction", default="unknown",
                    choices=["increased_gene_increases_risk",
                             "decreased_gene_increases_risk", "unknown"])
parser.add_argument("--fda_only", default="true", choices=["true","false"])
parser.add_argument("--include_safety_drugs", default="true", choices=["true","false"])
parser.add_argument("--output_dir", default="results")
parser.add_argument("--use_local", default="false", choices=["true","false"],
                    help="Use local PubMedBERT model instead of Claude API")
args = parser.parse_args()

df = run_pipeline(
    gene=args.gene, disease=args.disease,
    risk_direction=args.risk_direction,
    fda_only=(args.fda_only == "true"),
    include_safety_drugs=(args.include_safety_drugs == "true"),
    output_dir=args.output_dir,
    use_local=(args.use_local == "true")
)
try:
    print("\nTop results:")
    cols = ["drug","fda_approved","mechanism","direction","therapeutic_class","priority_score","priority_tier"]
    if len(df) > 0 and all(c in df.columns for c in cols):
        print(df[cols].head(10).to_string(index=False))
    else:
        print("  No FDA-approved drug-gene pairs found for this gene.")
except Exception as e:
    print(f"  Could not display results: {e}")
