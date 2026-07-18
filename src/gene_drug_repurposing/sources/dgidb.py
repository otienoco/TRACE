import requests
from ..schemas import DrugGeneCandidate
from .. import config

QUERY = """
query getDrugInteractions($gene: String!) {
  genes(names: [$gene]) {
    nodes {
      name
      interactions {
        drug { name }
        interactionTypes { type }
        publications { pmid }
        sources { fullName }
      }
    }
  }
}
"""

def query_dgidb(gene: str) -> list:
    candidates = []
    try:
        resp = requests.post(
            config.DGIDB_GRAPHQL_URL,
            json={"query": QUERY, "variables": {"gene": gene}},
            headers={"Content-Type": "application/json"},
            timeout=30
        )
        resp.raise_for_status()
        nodes = resp.json().get("data", {}).get("genes", {}).get("nodes", [])
        for node in nodes:
            for interaction in node.get("interactions", []):
                drug_name = interaction.get("drug", {}).get("name", "")
                if not drug_name:
                    continue
                itype = ", ".join(t.get("type", "") for t in interaction.get("interactionTypes", []) if t.get("type"))
                pmids = [str(p["pmid"]) for p in interaction.get("publications", []) if p.get("pmid")]
                sources = [s.get("fullName", "") for s in interaction.get("sources", [])]
                candidates.append(DrugGeneCandidate(
                    gene=gene, drug=drug_name, source_database="DGIdb",
                    interaction_type=itype if itype else None, pmids=pmids,
                    source_url=f"https://dgidb.org/genes/{gene}",
                    raw_annotation=f"Sources: {'; '.join(sources)}" if sources else None
                ))
    except Exception as e:
        print(f"[dgidb] ERROR: {e}")
    print(f"[dgidb] Found {len(candidates)} candidates for {gene}")
    return candidates
