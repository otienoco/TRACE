import requests
from ..schemas import DrugRecord
from .. import config

def check_fda_approval(drug_name: str) -> DrugRecord:
    drug_clean = drug_name.strip().lower()
    record = DrugRecord(drug_name=drug_name, normalized_drug_name=drug_clean)
    fda_result = _query_openfda(drug_clean)
    if fda_result:
        record.fda_approved_us = True
        record.approval_source = "openFDA"
        record.approval_confidence = "high"
        record.brand_names = fda_result.get("brand_names", [])
        record.normalized_drug_name = fda_result.get("generic_name", drug_clean)
        return record
    rxnorm_result = _query_rxnorm(drug_clean)
    if rxnorm_result:
        record.rxnorm_id = rxnorm_result.get("rxcui")
        record.normalized_drug_name = rxnorm_result.get("name", drug_clean).lower()
        record.brand_names = rxnorm_result.get("brand_names", [])
        record.fda_approved_us = None
        record.approval_source = "RxNorm"
        record.approval_confidence = "medium"
        return record
    record.fda_approved_us = None
    record.approval_confidence = "unknown"
    return record

def _query_openfda(drug_name):
    for q in [f'openfda.generic_name:"{drug_name}"', f'openfda.brand_name:"{drug_name}"']:
        try:
            resp = requests.get(f"{config.OPENFDA_BASE_URL}/label.json",
                                params={"search": q, "limit": 1}, timeout=15)
            if resp.status_code == 200:
                results = resp.json().get("results", [])
                if results:
                    openfda = results[0].get("openfda", {})
                    generic = openfda.get("generic_name", [])
                    brands  = openfda.get("brand_name", [])
                    return {"generic_name": generic[0].lower() if generic else drug_name,
                            "brand_names": [b.title() for b in brands]}
        except Exception as e:
            print(f"[fda] openFDA error: {e}")
    return None

def _query_rxnorm(drug_name):
    try:
        resp = requests.get(f"{config.RXNORM_BASE_URL}/rxcui.json",
                            params={"name": drug_name, "search": 1}, timeout=10)
        resp.raise_for_status()
        rxcui = resp.json().get("idGroup", {}).get("rxnormId", [None])[0]
        if not rxcui:
            return None
        resp2 = requests.get(f"{config.RXNORM_BASE_URL}/rxcui/{rxcui}/related.json",
                             params={"tty": "BN"}, timeout=10)
        resp2.raise_for_status()
        brand_names = [c.get("name", "") for group in
                       resp2.json().get("relatedGroup", {}).get("conceptGroup", [])
                       for c in group.get("conceptProperties", [])]
        return {"rxcui": rxcui, "name": drug_name, "brand_names": brand_names}
    except Exception as e:
        print(f"[fda] RxNorm error: {e}")
    return None
