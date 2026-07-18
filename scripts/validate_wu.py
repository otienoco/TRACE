"""
Validation against Wu et al. 2022, Nature Communications
Drug repurposing for hyperlipidemia and hypertension
"""
import pandas as pd
import os

# Novel repurposing candidates from Wu et al. Table 2
# Drugs approved for OTHER diseases that showed therapeutic effects
GOLD_STANDARD = {
    # Hyperlipidemia novel candidates (not statins)
    ("PCSK9",  "tamoxifen"):       "candidate_therapeutic_pair",
    ("PCSK9",  "digoxin"):         "candidate_therapeutic_pair",
    ("PCSK9",  "valproate"):       "candidate_therapeutic_pair",
    ("LDLR",   "tamoxifen"):       "candidate_therapeutic_pair",
    ("HMGCR",  "valproate"):       "candidate_therapeutic_pair",
    # Hypertension novel candidates
    ("ACE",    "estradiol"):       "candidate_therapeutic_pair",
    ("ACE",    "phenytoin"):       "candidate_therapeutic_pair",
    ("ACE",    "celecoxib"):       "candidate_therapeutic_pair",
    ("ACE",    "sertraline"):      "candidate_therapeutic_pair",
    ("ACE",    "rosiglitazone"):   "candidate_therapeutic_pair",
    ("ACE",    "simvastatin"):     "candidate_therapeutic_pair",
    ("ACE",    "atorvastatin"):    "candidate_therapeutic_pair",
    ("ADRB1",  "estradiol"):       "candidate_therapeutic_pair",
    ("ADRB1",  "phenytoin"):       "candidate_therapeutic_pair",
    ("ADRB1",  "celecoxib"):       "candidate_therapeutic_pair",
}

DRUG_ALIASES = {
    "valproate": ["valproate", "valproic acid", "valproic acid sodium"],
    "rosiglitazone": ["rosiglitazone", "rosiglitazone maleate"],
}

RESULTS_DIR = "results"

def load_results(gene, disease):
    path = os.path.join(RESULTS_DIR, f"{gene}_{disease}_prioritized_drugs.csv")
    if not os.path.exists(path):
        return None
    return pd.read_csv(path)

def check_pair(df, gene, drug):
    if df is None:
        return None, None
    names = DRUG_ALIASES.get(drug, [drug])
    for name in names:
        matches = df[df["drug"].str.lower() == name.lower()]
        if not matches.empty:
            return True, matches.iloc[0]["therapeutic_class"]
    return False, None

print("=" * 70)
print("EXTERNAL VALIDATION: Wu et al. 2022, Nature Communications")
print("Hyperlipidemia and Hypertension Drug Repurposing")
print("=" * 70)

# Load results
results = {}
for gene, disease in [("PCSK9","hyperlipidemia"), ("LDLR","hyperlipidemia"),
                       ("HMGCR","hyperlipidemia"), ("ACE","hypertension"),
                       ("ADRB1","hypertension")]:
    key = f"{gene}_{disease}"
    results[key] = load_results(gene, disease)
    status = "✅ loaded" if results[key] is not None else "❌ missing"
    print(f"  {gene} ({disease}): {status}")

print(f"\n{'Gene':<10} {'Drug':<30} {'Status'}")
print("-" * 65)

found = correct = 0
total = len(GOLD_STANDARD)

for (gene, drug), expected in sorted(GOLD_STANDARD.items()):
    disease = "hyperlipidemia" if gene in ["PCSK9","LDLR","HMGCR"] else "hypertension"
    key = f"{gene}_{disease}"
    f, cls = check_pair(results.get(key), gene, drug)
    if f is None:
        status = "NO FILE"
    elif f:
        found += 1
        if "candidate" in str(cls):
            correct += 1
            status = f"✓ CORRECT"
        else:
            status = f"~ FOUND: {cls}"
    else:
        status = "✗ NOT FOUND"
    print(f"{gene:<10} {drug:<30} {status}")

print("\n" + "=" * 70)
print("SUMMARY")
print("=" * 70)
print(f"Total gold standard pairs: {total}")
print(f"Found in pipeline:         {found}/{total} = {found/total*100:.1f}%")
print(f"Correctly classified:      {correct}/{total} = {correct/total*100:.1f}%")
