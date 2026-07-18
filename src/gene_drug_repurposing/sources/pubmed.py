import time
import requests
import xml.etree.ElementTree as ET
from ..schemas import EvidenceText
from .. import config

def retrieve_pubmed_evidence(gene: str, drug: str, extra_pmids: list = None) -> list:
    queries = [
        f'"{drug}"[tiab] AND "{gene}"[tiab]',
        f'"{drug}"[tiab] AND "{gene}"[tiab] AND (inhibit* OR antagonist OR agonist OR expression)',
    ]
    collected_pmids = {}
    for query in queries:
        for pmid in _esearch(query):
            if pmid not in collected_pmids:
                collected_pmids[pmid] = query
    if extra_pmids:
        for pmid in extra_pmids:
            if pmid and pmid not in collected_pmids:
                collected_pmids[pmid] = "database_annotation"
    if not collected_pmids:
        return []
    records = _efetch(list(collected_pmids.keys()))
    evidence = []
    for rec in records:
        text = ((rec.get("abstract") or "") + " " + (rec.get("title") or "")).lower()
        evidence.append(EvidenceText(
            pmid=rec.get("pmid"), title=rec.get("title"),
            abstract=rec.get("abstract"), journal=rec.get("journal"),
            year=rec.get("year"), query_used=collected_pmids.get(rec.get("pmid"), "unknown"),
            gene_mentioned=gene.lower() in text,
            drug_mentioned=drug.lower() in text, source="PubMed"
        ))
    filtered = [e for e in evidence if e.gene_mentioned and e.drug_mentioned]
    print(f"[pubmed] {gene} + {drug}: {len(filtered)} abstracts")
    return filtered

def _esearch(query, max_results=10):
    params = {"db": "pubmed", "term": query, "retmax": max_results, "retmode": "json"}
    if config.NCBI_API_KEY:
        params["api_key"] = config.NCBI_API_KEY
    try:
        resp = requests.get(f"{config.PUBMED_BASE_URL}/esearch.fcgi", params=params, timeout=15)
        resp.raise_for_status()
        time.sleep(0.34 if not config.NCBI_API_KEY else 0.1)
        return resp.json().get("esearchresult", {}).get("idlist", [])
    except Exception as e:
        print(f"[pubmed] esearch error: {e}")
        return []

def _efetch(pmids):
    if not pmids:
        return []
    params = {"db": "pubmed", "id": ",".join(pmids), "rettype": "xml", "retmode": "xml"}
    if config.NCBI_API_KEY:
        params["api_key"] = config.NCBI_API_KEY
    try:
        resp = requests.get(f"{config.PUBMED_BASE_URL}/efetch.fcgi", params=params, timeout=30)
        resp.raise_for_status()
        time.sleep(0.34 if not config.NCBI_API_KEY else 0.1)
        return _parse_xml(resp.text)
    except Exception as e:
        print(f"[pubmed] efetch error: {e}")
        return []

def _parse_xml(xml_text):
    records = []
    try:
        root = ET.fromstring(xml_text)
        for article in root.findall(".//PubmedArticle"):
            pmid_el     = article.find(".//PMID")
            title_el    = article.find(".//ArticleTitle")
            abstract_el = article.find(".//AbstractText")
            journal_el  = article.find(".//Journal/Title")
            year_el     = article.find(".//PubDate/Year")
            records.append({
                "pmid":     pmid_el.text if pmid_el is not None else None,
                "title":    "".join(title_el.itertext()) if title_el is not None else None,
                "abstract": "".join(abstract_el.itertext()) if abstract_el is not None else None,
                "journal":  journal_el.text if journal_el is not None else None,
                "year":     int(year_el.text) if year_el is not None else None,
            })
    except Exception as e:
        print(f"[pubmed] XML parse error: {e}")
    return records
