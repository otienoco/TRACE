"""
External validation against MASLD drug repurposing paper (Seagle et al. 2025)
Table S2a: Genes from TWAS mapped to drug targets
"""
import pandas as pd
import os

# Gold standard from Table S2a
GOLD_STANDARD = {
    ("ABCB11", "odevixibat"):                  "candidate_therapeutic_pair",
    ("ABCC2",  "sulfinpyrazone"):               "candidate_therapeutic_pair",
    ("ALDH2",  "disulfiram"):                   "candidate_therapeutic_pair",
    ("APOE",   "prednisone"):                   "candidate_therapeutic_pair",
    ("CPN1",   "osilodrostat phosphate"):       "candidate_therapeutic_pair",
    ("CPN1",   "levoketoconazole"):             "candidate_therapeutic_pair",
    ("FADS3",  "fish oil"):                     "candidate_therapeutic_pair",
    ("FLT1",   "nintedanib esylate"):           "candidate_therapeutic_pair",
    ("MYH7B",  "mavacamten"):                   "candidate_therapeutic_pair",
    ("PPARG",  "pioglitazone hydrochloride"):   "candidate_therapeutic_pair",
    ("PPARG",  "balsalazide disodium"):         "candidate_therapeutic_pair",
    ("PPARG",  "olsalazine sodium"):            "candidate_therapeutic_pair",
    ("PPARG",  "mesalamine"):                   "candidate_therapeutic_pair",
    ("SCN2A",  "eslicarbazepine acetate"):      "candidate_therapeutic_pair",
    ("SCN2A",  "oxcarbazepine"):                "candidate_therapeutic_pair",
    ("SCN2A",  "zonisamide"):                   "candidate_therapeutic_pair",
    ("SCN2A",  "carbamazepine"):                "candidate_therapeutic_pair",
    ("SCN2A",  "phenytoin"):                    "candidate_therapeutic_pair",
    ("SCN2A",  "lamotrigine"):                  "candidate_therapeutic_pair",
    ("SCN2A",  "topiramate"):                   "candidate_therapeutic_pair",
    ("SCN2A",  "lidocaine hydrochloride"):      "candidate_therapeutic_pair",
    ("SCN2A",  "riluzole"):                     "candidate_therapeutic_pair",
    ("SCN2A",  "cenobamate"):                   "candidate_therapeutic_pair",
    ("SCN2A",  "rufinamide"):                   "candidate_therapeutic_pair",
    ("SCN2A",  "mexiletine hydrochloride"):     "candidate_therapeutic_pair",
    ("SCN2A",  "quinidine"):                    "candidate_therapeutic_pair",
    ("SCN2A",  "procainamide hydrochloride"):   "candidate_therapeutic_pair",
    ("SCN2A",  "propafenone hydrochloride"):    "candidate_therapeutic_pair",
    ("SCN2A",  "dronedarone hydrochloride"):    "candidate_therapeutic_pair",
    ("S1PR2",  "fingolimod hydrochloride"):     "candidate_therapeutic_pair",
    ("VEGFA",  "faricimab"):                    "candidate_therapeutic_pair",
    ("VEGFA",  "ranibizumab"):                  "candidate_therapeutic_pair",
    ("VEGFA",  "aflibercept"):                  "candidate_therapeutic_pair",
    ("VEGFA",  "brolucizumab"):                 "candidate_therapeutic_pair",
}

DRUG_ALIASES = {
    "fingolimod hydrochloride": ["fingolimod hydrochloride", "fingolimod"],
    "pioglitazone hydrochloride": ["pioglitazone hydrochloride", "pioglitazone"],
    "sulfinpyrazone": ["sulfinpyrazone", "sulphinpyrazone"],
    "nintedanib esylate": ["nintedanib esylate", "nintedanib"],
    "lidocaine hydrochloride": ["lidocaine hydrochloride", "lidocaine"],
    "mexiletine hydrochloride": ["mexiletine hydrochloride", "mexiletine"],
    "procainamide hydrochloride": ["procainamide hydrochloride", "procainamide"],
    "propafenone hydrochloride": ["propafenone hydrochloride", "propafenone"],
    "dronedarone hydrochloride": ["dronedarone hydrochloride", "dronedarone"],
    "osilodrostat phosphate": ["osilodrostat phosphate", "osilodrostat"],
}

RESULTS_DIR = "results"

def load_results(gene):
    path = os.path.join(RESULTS_DIR, f"{gene}_MASLD_prioritized_drugs.csv")
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
print("EXTERNAL VALIDATION: MASLD Drug Repurposing (Seagle et al. 2025)")
print("=" * 70)

results = {}
genes = set(g for g, _ in GOLD_STANDARD.keys())
for gene in genes:
    results[gene] = load_results(gene)
    status = "✅ loaded" if results[gene] is not None else "❌ missing"
    print(f"  {gene}: {status}")

print(f"\n{'Gene':<10} {'Drug':<40} {'Status'}")
print("-" * 80)

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
    print(f"{gene:<10} {drug:<40} {status}")

print("\n" + "=" * 70)
print("SUMMARY")
print("=" * 70)
print(f"Total gold standard pairs: {total}")
print(f"Found in pipeline:         {found}/{total} = {found/total*100:.1f}%")
print(f"Correctly classified:      {correct}/{total} = {correct/total*100:.1f}%")
