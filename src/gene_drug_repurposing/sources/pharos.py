import requests
from ..schemas import DrugGeneCandidate

PHAROS_URL = "https://pharos-api.ncats.io/graphql"

def query_pharos(gene: str) -> list:
    candidates = []
    try:
        query = """
        {
          target(q: {sym: "%s"}) {
            sym
            ligands(isdrug: true) {
              ligid
              name
            }
          }
        }
        """ % gene
        resp = requests.post(
            PHAROS_URL,
            json={"query": query},
            headers={"Content-Type": "application/json"},
            timeout=30
        )
        resp.raise_for_status()
        target = resp.json().get("data", {}).get("target")
        if not target:
            print(f"[pharos] No target found for {gene}")
            return candidates
        for ligand in target.get("ligands", []):
            drug_name = ligand.get("name", "").strip().lower()
            if not drug_name:
                continue
            candidates.append(DrugGeneCandidate(
                gene=gene,
                drug=drug_name,
                source_database="Pharos",
                interaction_type=None,
                source_url=f"https://pharos.nih.gov/targets/{gene}",
                raw_annotation=None
            ))
    except Exception as e:
        print(f"[pharos] ERROR: {e}")
    print(f"[pharos] Found {len(candidates)} candidates for {gene}")
    return candidates
