import pandas as pd
import os

GOLD_STANDARD = {
    ("ACE",     "lisinopril"):          "candidate_therapeutic_pair",
    ("ACE",     "enalapril"):           "candidate_therapeutic_pair",
    ("ACE",     "benazepril"):          "candidate_therapeutic_pair",
    ("ACE",     "ramipril"):            "candidate_therapeutic_pair",
    ("KCNJ11",  "minoxidil"):           "candidate_therapeutic_pair",
    ("KCNJ11",  "verapamil"):           "candidate_therapeutic_pair",
    ("TH",      "metyrosine"):          "candidate_therapeutic_pair",
    ("CACNA1A", "verapamil"):           "candidate_therapeutic_pair",
    ("GCK",     "sitaxentan"):          "candidate_therapeutic_pair",
    ("HCN3",    "ivabradine"):          "candidate_therapeutic_pair",
    ("SCN3A",   "lamotrigine"):         "candidate_therapeutic_pair",
    ("SCN3A",   "carbamazepine"):       "candidate_therapeutic_pair",
    ("SCN3A",   "phenytoin"):           "candidate_therapeutic_pair",
    ("SCN3A",   "oxcarbazepine"):       "candidate_therapeutic_pair",
    ("MAPK3",   "sulindac"):            "candidate_therapeutic_pair",
    ("BCL2",    "isosorbide"):          "candidate_therapeutic_pair",
    ("IKBKE",   "amlexanox"):           "candidate_therapeutic_pair",
    ("OPRL1",   "buprenorphine"):       "candidate_therapeutic_pair",
    ("OPRL1",   "naloxone"):            "candidate_therapeutic_pair",
    ("OPRL1",   "naltrexone"):          "candidate_therapeutic_pair",
}

DRUG_ALIASES = {
    "verapamil":  ["verapamil", "verapamil hydrochloride"],
    "isosorbide": ["isosorbide", "isosorbide dinitrate", "isosorbide mononitrate"],
    "ivabradine": ["ivabradine", "ivabradine hydrochloride"],
    "naltrexone": ["naltrexone", "naltrexone hydrochloride"],
    "naloxone":   ["naloxone", "naloxone hydrochloride"],
    "buprenorphine": ["buprenorphine", "buprenorphine hydrochloride"],
}

RESULTS_DIR = "results"

def load_results(gene):
    path = os.path.join(RESULTS_DIR, f"{gene}_T2D_prioritized_drugs.csv")
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
print("EXTERNAL VALIDATION: T2D Drug Repurposing (Shuey et al. 2023)")
print("=" * 70)

results = {}
genes = set(g for g, _ in GOLD_STANDARD.keys())
for gene in genes:
    results[gene] = load_results(gene)
    status = "✅ loaded" if results[gene] is not None else "❌ missing"
    print(f"  {gene}: {status}")

print(f"\n{'Gene':<10} {'Drug':<35} {'Status'}")
print("-" * 70)

found = 0
correct = 0
total = len(GOLD_STANDARD)

for (gene, drug), expected_class in sorted(GOLD_STANDARD.items()):
    f, classification = check_pair(results.get(gene), gene, drug)
    if f is None:
        status = "NO FILE"
    elif f:
        found += 1
        if "candidate" in str(classification):
            correct += 1
            status = f"✓ CORRECT"
        else:
            status = f"~ FOUND: {classification}"
    else:
        status = "✗ NOT FOUND"
    print(f"{gene:<10} {drug:<35} {status}")

print("\n" + "=" * 70)
print("SUMMARY")
print("=" * 70)
print(f"Total gold standard pairs: {total}")
print(f"Found in pipeline:         {found}/{total} = {found/total*100:.1f}%")
print(f"Correctly classified:      {correct}/{total} = {correct/total*100:.1f}%")
