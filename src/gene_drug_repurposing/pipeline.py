import json, os
import pandas as pd
from datetime import datetime
from .schemas import DrugGenePair
from .gene_normalization.normalize_gene import normalize_gene
from .sources.dgidb import query_dgidb
from .sources.opentargets import query_opentargets
from .sources.ctd import query_ctd
from .sources.pharos import query_pharos
from .sources.pubmed import retrieve_pubmed_evidence
from .sources.fda import check_fda_approval
from .evidence.classify_hybrid import classify_evidence_batch_hybrid
from .directionality.classify_direction import classify_therapeutic_direction, normalize_mechanism_string
from .scoring.score_pair import score_pair, aggregate_evidence
from . import config

def run_pipeline(gene, disease=None, risk_direction="unknown", fda_only=True,
                 include_safety_drugs=True, output_dir="results", use_local=False):
    os.makedirs(output_dir, exist_ok=True)
    label = f"{gene.upper()}{'_' + disease.replace(' ', '_') if disease else ''}"
    mode  = "LOCAL MODEL" if use_local else "CLAUDE API + LOCAL COMPARISON"
    print(f"\n{'='*60}")
    print(f"Gene-to-Drug Repurposing Pipeline")
    print(f"Gene: {gene} | Disease: {disease or 'not specified'}")
    print(f"Risk direction: {risk_direction}")
    print(f"Classification mode: {mode}")
    print(f"{'='*60}\n")

    print("[Step 1] Normalizing gene...")
    gene_record     = normalize_gene(gene)
    official_symbol = gene_record.official_symbol
    print(f"  -> {gene_record.input_gene} resolved to {official_symbol}")

    print("[Step 2] Querying drug databases...")
    all_candidates  = []
    all_candidates += query_dgidb(official_symbol)
    all_candidates += query_opentargets(official_symbol, ensembl_id=gene_record.ensembl_id)
    all_candidates += query_ctd(official_symbol)
    all_candidates += query_pharos(official_symbol)
    print(f"  -> Total raw candidates: {len(all_candidates)}")

    print("[Step 3] Deduplicating...")
    drug_map = {}
    for c in all_candidates:
        drug_map.setdefault(c.drug.strip().lower(), []).append(c)
    print(f"  -> Unique drugs: {len(drug_map)}")

    print("[Step 4] FDA check first...")
    fda_cache        = {}
    approved_drug_map = {}
    for drug_key, candidates in drug_map.items():
        drug_record = check_fda_approval(drug_key)
        fda_cache[drug_key] = drug_record
        if fda_only and drug_record.fda_approved_us is not True:
            continue
        approved_drug_map[drug_key] = candidates
    print(f"  -> {len(approved_drug_map)} drugs pass FDA filter (from {len(drug_map)} total)")

    pairs = []
    for drug_key, candidates in approved_drug_map.items():
        print(f"\n  Processing: {drug_key}")
        drug_record = fda_cache[drug_key]
        source_dbs  = list({c.source_database for c in candidates})
        known_pmids = list({p for c in candidates for p in c.pmids})
        raw_mech    = candidates[0].interaction_type if candidates else None
        norm_mech   = normalize_mechanism_string(raw_mech)

        pair = DrugGenePair(
            gene=official_symbol, drug=drug_key,
            gene_record=gene_record, drug_record=drug_record,
            source_databases=source_dbs, raw_candidates=candidates,
            fda_approved=drug_record.fda_approved_us, consensus_mechanism=norm_mech
        )

        print(f"    -> Fetching PubMed evidence...")
        pair.evidence_texts = retrieve_pubmed_evidence(
            official_symbol, drug_key, extra_pmids=known_pmids
        )

        if pair.evidence_texts:
            print(f"    -> Classifying {len(pair.evidence_texts)} abstract(s) [{mode}]...")
            pair.evidence_classifications = classify_evidence_batch_hybrid(
                pair.evidence_texts, official_symbol, drug_key, use_local=use_local
            )
        else:
            pair.evidence_classifications = []

        pair = aggregate_evidence(pair)
        pair.therapeutic_classification, pair.manual_review_flag = \
            classify_therapeutic_direction(
                risk_direction, pair.consensus_mechanism, pair.consensus_direction
            )
        pair = score_pair(pair)

        if not include_safety_drugs and \
                pair.therapeutic_classification == "potential_safety_concern":
            continue
        pairs.append(pair)

    pairs.sort(key=lambda p: p.priority_score, reverse=True)
    print(f"\n[Step 5] Ranked {len(pairs)} drug-gene pairs.")

    df = pd.DataFrame([{
        "gene":               p.gene,
        "drug":               p.drug,
        "fda_approved":       p.fda_approved,
        "brand_names":        ", ".join(p.drug_record.brand_names) if p.drug_record else "",
        "source_databases":   ", ".join(p.source_databases),
        "mechanism":          p.consensus_mechanism,
        "direction":          p.consensus_direction,
        "evidence_strength":  p.consensus_evidence_strength,
        "therapeutic_class":  p.therapeutic_classification,
        "priority_score":     p.priority_score,
        "priority_tier":      p.priority_tier,
        "supporting_pmids":   ", ".join(p.supporting_pmids),
        "manual_review_flag": p.manual_review_flag,
        "rationale":          p.rationale,
    } for p in pairs])

    csv_path  = os.path.join(output_dir, f"{label}_prioritized_drugs.csv")
    json_path = os.path.join(output_dir, f"{label}_evidence.json")
    md_path   = os.path.join(output_dir, f"{label}_report.md")

    df.to_csv(csv_path, index=False)
    with open(json_path, "w") as f:
        json.dump([p.to_dict() for p in pairs], f, indent=2, default=str)
    lines = [
        f"# Gene-to-Drug Repurposing Report",
        f"**Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M')}",
        f"**Gene:** {official_symbol} | **Disease:** {disease or 'N/A'} | "
        f"**Risk direction:** {risk_direction}",
        f"**Classification mode:** {mode}", "",
        "| Drug | FDA | Mechanism | Direction | Class | Score | Tier | Databases |",
        "|------|-----|-----------|-----------|-------|-------|------|-----------|"
    ]
    for p in pairs:
        lines.append(
            f"| {p.drug} | {p.fda_approved} | {p.consensus_mechanism} | "
            f"{p.consensus_direction} | {p.therapeutic_classification} | "
            f"{p.priority_score} | {p.priority_tier} | "
            f"{', '.join(p.source_databases)} |"
        )
    lines.append("\n---\n*Research purposes only. Requires experimental validation.*")
    with open(md_path, "w") as f:
        f.write("\n".join(lines))

    print(f"[Output] CSV  -> {csv_path}")
    print(f"[Output] JSON -> {json_path}")
    print(f"[Output] MD   -> {md_path}")
    return df
