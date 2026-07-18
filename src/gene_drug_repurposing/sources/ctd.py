import requests
import gzip
import os
from ..schemas import DrugGeneCandidate

CTD_URL    = "https://ctdbase.org/reports/CTD_chem_gene_ixns.tsv.gz"
CACHE_PATH = "data/raw/CTD_chem_gene_ixns.tsv.gz"

PHARMACOLOGICAL_KEYWORDS = [
    "increases^expression", "decreases^expression",
    "increases^activity", "decreases^activity",
    "increases^binding", "decreases^binding",
    "affects^binding", "increases^reaction",
    "decreases^reaction", "increases^abundance",
    "decreases^abundance", "affects^expression",
    "affects^activity", "increases^phosphorylation",
    "decreases^phosphorylation", "increases^degradation",
    "decreases^degradation", "increases^stability",
    "decreases^stability", "increases^methylation",
    "decreases^methylation",
]

def _is_pharmacological(interaction: str) -> bool:
    if not interaction:
        return False
    return any(k in interaction.lower() for k in PHARMACOLOGICAL_KEYWORDS)

def query_ctd(gene: str) -> list:
    candidates = []
    total_seen = 0
    total_kept = 0
    try:
        _ensure_cache()
        with gzip.open(CACHE_PATH, "rt", encoding="utf-8", errors="replace") as f:
            for line in f:
                if line.startswith("#") or not line.strip():
                    continue
                parts = line.rstrip("\n").split("\t")
                row = dict(zip(
                    ["ChemicalName","ChemicalID","CasRN","GeneSymbol",
                     "GeneID","GeneForms","Organism","OrganismID",
                     "Interaction","InteractionActions","PubMedIDs"],
                    parts + [""] * 11
                ))
                if row.get("GeneSymbol", "").upper() != gene.upper():
                    continue
                if row.get("Organism", "") not in ("Homo sapiens", ""):
                    continue
                drug_name = row.get("ChemicalName", "").strip().lower()
                if not drug_name:
                    continue
                interaction = row.get("InteractionActions", "").strip()
                pmids_raw   = row.get("PubMedIDs", "").strip()
                pmids       = [p.strip() for p in pmids_raw.split("|") if p.strip()]
                total_seen += 1
                if not _is_pharmacological(interaction):
                    continue
                total_kept += 1
                candidates.append(DrugGeneCandidate(
                    gene=gene,
                    drug=drug_name,
                    source_database="CTD",
                    interaction_type=interaction if interaction else None,
                    pmids=pmids,
                    source_url=f"https://ctdbase.org/results.go?query={gene}&inputType=genesymbol",
                    raw_annotation=row.get("Interaction", "")
                ))
    except Exception as e:
        print(f"[ctd] ERROR: {e}")

    seen = {}
    for c in candidates:
        if c.drug not in seen:
            seen[c.drug] = c
        else:
            seen[c.drug].pmids = list(set(seen[c.drug].pmids + c.pmids))
    result = list(seen.values())
    print(f"[ctd] {gene}: saw {total_seen}, kept {total_kept}, {len(result)} unique drugs")
    return result

def _ensure_cache():
    if os.path.exists(CACHE_PATH) and os.path.getsize(CACHE_PATH) > 1000000:
        print(f"[ctd] Using cached file: {CACHE_PATH}")
        return
    print(f"[ctd] Downloading CTD bulk file (~40MB)...")
    os.makedirs(os.path.dirname(CACHE_PATH), exist_ok=True)
    resp = requests.get(CTD_URL, stream=True, timeout=120)
    resp.raise_for_status()
    with open(CACHE_PATH, "wb") as f:
        for chunk in resp.iter_content(chunk_size=65536):
            f.write(chunk)
    print(f"[ctd] Download complete: {CACHE_PATH}")
