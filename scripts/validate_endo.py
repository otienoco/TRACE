"""
Validate pipeline results against manually curated endometriosis benchmark.
Handles drug name variants (salt forms, formulations).
"""
import pandas as pd
import os

# Drug name aliases - maps gold standard names to pipeline names
DRUG_ALIASES = {
    "follitropin delta":          ["follitropin delta", "follitropin"],
    "urofollitropin":             ["urofollitropin", "follicle stimulating hormone"],
    "corifollitropin alfa":       ["corifollitropin alfa", "corifollitropin"],
    "follitropin beta":           ["follitropin beta", "follitropin"],
    "follitropin alfa":           ["follitropin alfa", "follitropin"],
    "cabozantinib s-malate":      ["cabozantinib s-malate", "cabozantinib"],
    "lenvatinib mesylate":        ["lenvatinib mesylate", "lenvatinib"],
    "sorafenib tosylate":         ["sorafenib tosylate", "sorafenib"],
    "sunitinib malate":           ["sunitinib malate", "sunitinib"],
    "tivozanib hydrochloride":    ["tivozanib hydrochloride", "tivozanib"],
    "medroxyprogesterone acetate":["medroxyprogesterone acetate", "medroxyprogesterone"],
    "megestrol acetate":          ["megestrol acetate", "megestrol"],
    "estrogens, conjugated (usp)":["estrogens, conjugated (usp)", "estrogens, conjugated",
                                   "conjugated estrogens", "estrogens"],
    "medroxyprogesterone":        ["medroxyprogesterone", "medroxyprogesterone acetate"],
}

THERAPEUTIC_PAIRS = [
    ("FSHR",   "follitropin delta"),
    ("FSHR",   "urofollitropin"),
    ("FSHR",   "follicle stimulating hormone"),
    ("PGR",    "drospirenone"),
    ("PGR",    "ulipristal acetate"),
    ("PGR",    "dienogest"),
    ("PGR",    "progestin"),
    ("PGR",    "progesterone"),
    ("PGR",    "medroxyprogesterone"),
    ("PGR",    "medroxyprogesterone acetate"),
    ("PGR",    "tamoxifen"),
    ("PGR",    "danazol"),
    ("PGR",    "mifepristone"),
    ("PGR",    "progestogen"),
    ("PGR",    "estradiol"),
    ("PTGER4", "adalimumab"),
    ("PTGER4", "celecoxib"),
    ("PTGER4", "valproic acid"),
]

SAFETY_PAIRS = [
    ("CDKN2A", "palbociclib"),
    ("FSHR",   "corifollitropin alfa"),
    ("FSHR",   "follitropin"),
    ("FSHR",   "follitropin alfa"),
    ("FSHR",   "follitropin beta"),
    ("FSHR",   "follitropin delta"),
    ("GNRH1",  "estrogens, conjugated (usp)"),
    ("KDR",    "axitinib"),
    ("KDR",    "cabozantinib"),
    ("KDR",    "cabozantinib s-malate"),
    ("KDR",    "lenvatinib"),
    ("KDR",    "lenvatinib mesylate"),
    ("KDR",    "sorafenib tosylate"),
    ("KDR",    "sunitinib"),
    ("KDR",    "sunitinib malate"),
    ("KDR",    "tivozanib hydrochloride"),
    ("KDR",    "vandetanib"),
    ("PGR",    "anastrozole"),
    ("PGR",    "fulvestrant"),
    ("PGR",    "letrozole"),
    ("PGR",    "levonorgestrel"),
    ("PGR",    "megestrol"),
    ("PGR",    "megestrol acetate"),
    ("PGR",    "progesterone"),
    ("PGR",    "toremifene"),
]

RESULTS_DIR = "results"

def load_results(gene):
    path = os.path.join(RESULTS_DIR, f"{gene}_endometriosis_prioritized_drugs.csv")
    if not os.path.exists(path):
        print(f"  [MISSING] No results file for {gene}")
        return None
    return pd.read_csv(path)

def check_pair(df, gene, drug):
    if df is None:
        return None, None
    # Get all names to check including aliases
    names_to_check = DRUG_ALIASES.get(drug, [drug])
    for name in names_to_check:
        matches = df[df["drug"].str.lower() == name.lower()]
        if not matches.empty:
            return True, matches.iloc[0]["therapeutic_class"]
    return False, None

print("=" * 70)
print("ENDOMETRIOSIS VALIDATION REPORT")
print("=" * 70)

results = {}
for gene in ["FSHR", "PGR", "PTGER4", "CDKN2A", "KDR", "GNRH1"]:
    results[gene] = load_results(gene)

print("\n── THERAPEUTIC CANDIDATE PAIRS (Table 1) ──")
print(f"{'Gene':<10} {'Drug':<35} {'Status'}")
print("-" * 80)

therapeutic_found = 0
therapeutic_correct = 0

for gene, drug in THERAPEUTIC_PAIRS:
    found, classification = check_pair(results.get(gene), gene, drug)
    if found is None:
        status = "NO FILE"
    elif found:
        therapeutic_found += 1
        if "candidate" in str(classification):
            therapeutic_correct += 1
            status = f"✓ CORRECT ({classification})"
        else:
            status = f"~ FOUND but: {classification}"
    else:
        status = "✗ NOT FOUND"
    print(f"{gene:<10} {drug:<35} {status}")

print(f"\n── SAFETY/OPPOSITE-DIRECTION PAIRS (Table 3) ──")
print(f"{'Gene':<10} {'Drug':<35} {'Status'}")
print("-" * 80)

safety_found = 0
safety_correct = 0

for gene, drug in SAFETY_PAIRS:
    found, classification = check_pair(results.get(gene), gene, drug)
    if found is None:
        status = "NO FILE"
    elif found:
        safety_found += 1
        if "safety" in str(classification):
            safety_correct += 1
            status = f"✓ CORRECT ({classification})"
        else:
            status = f"~ FOUND but: {classification}"
    else:
        status = "✗ NOT FOUND"
    print(f"{gene:<10} {drug:<35} {status}")

print("\n" + "=" * 70)
print("SUMMARY METRICS")
print("=" * 70)
total_therapeutic = len(THERAPEUTIC_PAIRS)
total_safety = len(SAFETY_PAIRS)

print(f"Therapeutic pairs:")
print(f"  Recall (found):     {therapeutic_found}/{total_therapeutic} = {therapeutic_found/total_therapeutic*100:.1f}%")
print(f"  Correct class:      {therapeutic_correct}/{total_therapeutic} = {therapeutic_correct/total_therapeutic*100:.1f}%")
print(f"\nSafety pairs:")
print(f"  Recall (found):     {safety_found}/{total_safety} = {safety_found/total_safety*100:.1f}%")
print(f"  Correct class:      {safety_correct}/{total_safety} = {safety_correct/total_safety*100:.1f}%")
print(f"\nOverall recall:       {(therapeutic_found+safety_found)}/{total_therapeutic+total_safety} = {(therapeutic_found+safety_found)/(total_therapeutic+total_safety)*100:.1f}%")
print(f"Overall correct:      {(therapeutic_correct+safety_correct)}/{total_therapeutic+total_safety} = {(therapeutic_correct+safety_correct)/(total_therapeutic+total_safety)*100:.1f}%")
