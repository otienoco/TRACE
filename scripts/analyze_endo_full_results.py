"""
Full analysis of 99 endometriosis gene pipeline results vs manual review.
Reports:
1. Recovery of manually curated pairs
2. Novel candidates not in manual review
3. Summary statistics for paper
"""
import pandas as pd
import glob
import os

# ── Manual review gold standard ───────────────────────────────────────────────
MANUAL_THERAPEUTIC = [
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

MANUAL_SAFETY = [
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

DRUG_ALIASES = {
    "follitropin delta":           ["follitropin delta", "follitropin"],
    "follitropin beta":            ["follitropin beta", "follitropin"],
    "follitropin alfa":            ["follitropin alfa", "follitropin"],
    "urofollitropin":              ["urofollitropin", "follicle stimulating hormone"],
    "corifollitropin alfa":        ["corifollitropin alfa", "corifollitropin"],
    "cabozantinib s-malate":       ["cabozantinib s-malate", "cabozantinib"],
    "lenvatinib mesylate":         ["lenvatinib mesylate", "lenvatinib"],
    "sorafenib tosylate":          ["sorafenib tosylate", "sorafenib"],
    "sunitinib malate":            ["sunitinib malate", "sunitinib"],
    "tivozanib hydrochloride":     ["tivozanib hydrochloride", "tivozanib"],
    "medroxyprogesterone acetate": ["medroxyprogesterone acetate", "medroxyprogesterone"],
    "megestrol acetate":           ["megestrol acetate", "megestrol"],
    "estrogens, conjugated (usp)": ["estrogens, conjugated (usp)", "estrogens, conjugated"],
}

# Non-drugs to exclude
NON_DRUGS = {
    "oxygen","lead","nickel","cadmium","manganese","copper","mercury",
    "arsenic","zinc","iron","aluminum","silicon","bisphenol a","ethanol",
    "glucose","sucrose","malathion","coumarin","ascorbic acid","resveratrol",
    "curcumin","hydrogen peroxide","smoke","cantharidin","formaldehyde",
    "arsenite","arsenic trioxide","aflatoxin b1","dactinomycin"
}

MANUAL_KNOWN = set(
    [(g.upper(), d.lower()) for g,d in MANUAL_THERAPEUTIC + MANUAL_SAFETY]
)

def load_all_results(results_dir="results", suffix="endometriosis"):
    all_files = glob.glob(f"{results_dir}/*{suffix}*prioritized_drugs.csv")
    all_dfs = []
    for f in all_files:
        gene = f.split("/")[-1].replace(f"_{suffix}_prioritized_drugs.csv","")
        try:
            df = pd.read_csv(f)
            if len(df) > 0:
                df["gene"] = gene
                all_dfs.append(df)
        except:
            pass
    if not all_dfs:
        return pd.DataFrame()
    return pd.concat(all_dfs, ignore_index=True)

def check_found(gene, drug, combined):
    names = DRUG_ALIASES.get(drug, [drug])
    for name in names:
        match = combined[
            (combined["gene"].str.upper() == gene.upper()) &
            (combined["drug"].str.lower() == name.lower())
        ]
        if len(match) > 0:
            return True, match.iloc[0]["therapeutic_class"]
    return False, None

def run_analysis(results_dir="results", suffix="endometriosis"):
    combined = load_all_results(results_dir, suffix)
    if combined.empty:
        print("No results found!")
        return

    # Filter non-drugs
    combined = combined[~combined["drug"].str.lower().isin(NON_DRUGS)]

    candidates = combined[combined["therapeutic_class"] == "candidate_therapeutic_pair"]
    safety     = combined[combined["therapeutic_class"] == "potential_safety_concern"]
    unclear    = combined[combined["therapeutic_class"] == "unclear_direction_manual_review"]

    print("=" * 70)
    print("FULL ENDOMETRIOSIS PIPELINE ANALYSIS")
    print("=" * 70)
    print(f"\nGenes with drug results:      {combined['gene'].nunique()}")
    print(f"Total drug-gene pairs:         {len(combined)}")
    print(f"Candidate therapeutic pairs:   {len(candidates)}")
    print(f"Potential safety concerns:     {len(safety)}")
    print(f"Unclear direction:             {len(unclear)}")
    print(f"Unique therapeutic drugs:      {candidates['drug'].nunique()}")
    print(f"Unique genes with candidates:  {candidates['gene'].nunique()}")

    # ── Section 1: Manual review recovery ────────────────────────────────────
    print("\n" + "=" * 70)
    print("SECTION 1: MANUAL REVIEW RECOVERY")
    print("=" * 70)

    print(f"\n{'Gene':<10} {'Drug':<35} {'Status'}")
    print("-" * 75)

    t_found = t_correct = 0
    for gene, drug in MANUAL_THERAPEUTIC:
        found, cls = check_found(gene, drug, combined)
        if found:
            t_found += 1
            if "candidate" in str(cls):
                t_correct += 1
                status = f"✓ CORRECT"
            else:
                status = f"~ FOUND: {cls}"
        else:
            status = "✗ NOT FOUND"
        print(f"{gene:<10} {drug:<35} {status}")

    print(f"\n{'Gene':<10} {'Drug':<35} {'Status'}")
    print("-" * 75)

    s_found = s_correct = 0
    for gene, drug in MANUAL_SAFETY:
        found, cls = check_found(gene, drug, combined)
        if found:
            s_found += 1
            if "safety" in str(cls):
                s_correct += 1
                status = f"✓ CORRECT"
            else:
                status = f"~ FOUND: {cls}"
        else:
            status = "✗ NOT FOUND"
        print(f"{gene:<10} {drug:<35} {status}")

    total = len(MANUAL_THERAPEUTIC) + len(MANUAL_SAFETY)
    print(f"\nTherapeutic recall:    {t_found}/18 = {t_found/18*100:.1f}%")
    print(f"Therapeutic correct:   {t_correct}/18 = {t_correct/18*100:.1f}%")
    print(f"Safety recall:         {s_found}/25 = {s_found/25*100:.1f}%")
    print(f"Safety correct:        {s_correct}/25 = {s_correct/25*100:.1f}%")
    print(f"Overall recall:        {t_found+s_found}/{total} = {(t_found+s_found)/total*100:.1f}%")
    print(f"Overall correct:       {t_correct+s_correct}/{total} = {(t_correct+s_correct)/total*100:.1f}%")

    # ── Section 2: Novel candidates ───────────────────────────────────────────
    print("\n" + "=" * 70)
    print("SECTION 2: NOVEL CANDIDATES (not in manual review)")
    print("=" * 70)

    novel_candidates = candidates[~candidates.apply(
        lambda r: (r["gene"].upper(), r["drug"].lower()) in MANUAL_KNOWN, axis=1
    )]
    novel_safety = safety[~safety.apply(
        lambda r: (r["gene"].upper(), r["drug"].lower()) in MANUAL_KNOWN, axis=1
    )]

    print(f"\nNOVEL THERAPEUTIC CANDIDATES:")
    print(f"{'Gene':<12} {'Drug':<30} {'Mechanism':<30} {'Direction':<25} {'Score'}")
    print("-" * 105)
    for _, row in novel_candidates.sort_values("priority_score", ascending=False).iterrows():
        print(f"{row['gene']:<12} {row['drug']:<30} {row['mechanism']:<30} {row['direction']:<25} {row['priority_score']}")

    print(f"\nNOVEL SAFETY CONCERNS:")
    print(f"{'Gene':<12} {'Drug':<30} {'Mechanism':<30} {'Direction':<25} {'Score'}")
    print("-" * 105)
    for _, row in novel_safety.sort_values("priority_score", ascending=False).head(20).iterrows():
        print(f"{row['gene']:<12} {row['drug']:<30} {row['mechanism']:<30} {row['direction']:<25} {row['priority_score']}")

    print(f"\nNovel therapeutic candidates: {len(novel_candidates)}")
    print(f"Novel safety concerns:        {len(novel_safety)}")
    print(f"Novel genes with findings:    {len(set(list(novel_candidates['gene']) + list(novel_safety['gene'])))}")

    # ── Section 3: Paper summary ──────────────────────────────────────────────
    print("\n" + "=" * 70)
    print("SECTION 3: PAPER SUMMARY NUMBERS")
    print("=" * 70)
    print(f"Total genes queried:           99")
    print(f"Genes with drug hits:          {combined['gene'].nunique()}")
    print(f"Genes with no drug hits:       {99 - combined['gene'].nunique()} (non-coding RNAs)")
    print(f"Total FDA-approved pairs:      {len(combined)}")
    print(f"Candidate therapeutic pairs:   {len(candidates)}")
    print(f"Novel candidates:              {len(novel_candidates)}")
    print(f"Manual review recovery:        {t_found+s_found}/{total} = {(t_found+s_found)/total*100:.1f}%")

if __name__ == "__main__":
    run_analysis()
