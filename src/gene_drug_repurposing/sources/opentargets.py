import requests
from ..schemas import DrugGeneCandidate

OT_URL = "https://api.platform.opentargets.org/api/v4/graphql"

def query_opentargets(gene: str, ensembl_id: str = None) -> list:
    candidates = []
    if not ensembl_id:
        ensembl_id = _resolve_ensembl_id(gene)
    if not ensembl_id:
        print(f"[opentargets] Could not resolve Ensembl ID for {gene}. Skipping.")
        return candidates
    try:
        query = """
        {
          target(ensemblId: "%s") {
            approvedSymbol
            drugAndClinicalCandidates {
              rows {
                drug { id name }
                maxClinicalStage
              }
            }
          }
        }
        """ % ensembl_id
        resp = requests.post(
            OT_URL,
            json={"query": query},
            headers={"Content-Type": "application/json"},
            timeout=30
        )
        resp.raise_for_status()
        target = resp.json().get("data", {}).get("target")
        if not target:
            print(f"[opentargets] No target data for {gene}")
            return candidates
        for row in target.get("drugAndClinicalCandidates", {}).get("rows", []):
            drug_name = row.get("drug", {}).get("name", "").lower()
            if not drug_name:
                continue
            stage = row.get("maxClinicalStage", "")
            candidates.append(DrugGeneCandidate(
                gene=gene,
                drug=drug_name,
                source_database="OpenTargets",
                interaction_type=None,
                evidence_level=stage if stage else None,
                source_url=f"https://platform.opentargets.org/target/{ensembl_id}",
                raw_annotation=stage
            ))
    except Exception as e:
        print(f"[opentargets] ERROR: {e}")
    print(f"[opentargets] Found {len(candidates)} candidates for {gene}")
    return candidates

def _resolve_ensembl_id(gene_symbol):
    query = """
    {
      search(queryString: "%s", entityNames: ["target"]) {
        hits {
          id
          object { ... on Target { approvedSymbol } }
        }
      }
    }
    """ % gene_symbol
    try:
        resp = requests.post(
            OT_URL,
            json={"query": query},
            headers={"Content-Type": "application/json"},
            timeout=15
        )
        resp.raise_for_status()
        hits = resp.json().get("data", {}).get("search", {}).get("hits", [])
        for hit in hits:
            if hit.get("object", {}).get("approvedSymbol", "").upper() == gene_symbol.upper():
                return hit.get("id")
        if hits:
            return hits[0].get("id")
    except Exception as e:
        print(f"[opentargets] Ensembl ID resolution error: {e}")
    return None
