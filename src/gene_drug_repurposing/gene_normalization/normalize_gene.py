import requests
from ..schemas import GeneRecord
from .. import config

def normalize_gene(gene_input: str) -> GeneRecord:
    gene_input_clean = gene_input.strip()
    record = _hgnc_fetch_symbol(gene_input_clean)
    if record:
        return record
    record = _hgnc_search(gene_input_clean)
    if record:
        return record
    print(f"[gene_normalization] WARNING: Could not normalize '{gene_input}'. Using as-is.")
    return GeneRecord(input_gene=gene_input_clean, official_symbol=gene_input_clean.upper(), normalized=False)

def _hgnc_fetch_symbol(symbol):
    url = f"{config.HGNC_BASE_URL}/fetch/symbol/{symbol}"
    try:
        resp = requests.get(url, headers={"Accept": "application/json"}, timeout=10)
        resp.raise_for_status()
        docs = resp.json().get("response", {}).get("docs", [])
        if docs:
            return _parse_hgnc_doc(symbol, docs[0])
    except Exception as e:
        print(f"[gene_normalization] HGNC symbol fetch error: {e}")
    return None

def _hgnc_search(query):
    url = f"{config.HGNC_BASE_URL}/search/{requests.utils.quote(query)}"
    try:
        resp = requests.get(url, headers={"Accept": "application/json"}, timeout=10)
        resp.raise_for_status()
        docs = resp.json().get("response", {}).get("docs", [])
        if docs:
            return _parse_hgnc_doc(query, docs[0])
    except Exception as e:
        print(f"[gene_normalization] HGNC search error: {e}")
    return None

def _parse_hgnc_doc(input_gene, doc):
    aliases = doc.get("alias_symbol", []) + doc.get("prev_symbol", []) + doc.get("alias_name", [])
    return GeneRecord(
        input_gene=input_gene,
        official_symbol=doc.get("symbol", input_gene.upper()),
        gene_id=str(doc.get("entrez_id", "")),
        ensembl_id=doc.get("ensembl_gene_id"),
        uniprot_id=doc.get("uniprot_ids", [None])[0] if doc.get("uniprot_ids") else None,
        aliases=list(set(aliases)),
        normalization_source="HGNC",
        normalized=True
    )
