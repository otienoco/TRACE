import json, re, requests
from ..schemas import EvidenceClassification
from .. import config

SYSTEM_PROMPT = """You are a biomedical text mining expert. Analyze scientific text and extract
structured information about how a drug affects a gene. Be conservative.
Only state what the text explicitly supports. Return ONLY valid JSON, no markdown."""

PROMPT_TEMPLATE = """Analyze this text for evidence of a relationship between drug "{drug}" and gene "{gene}".

TEXT: {text}

Return JSON with exactly these fields:
{{"supports_drug_gene_relationship": true/false, "directness": "direct/indirect/unclear",
"mechanism": "inhibitor/antagonist/agonist/activator/downregulator/upregulator/degrader/binder_only/modulator_unclear_direction/unknown",
"direction": "decreases_expression/increases_expression/decreases_activity/increases_activity/mixed/unclear/not_applicable",
"biological_level": "mRNA_expression/protein_expression/protein_activity/receptor_signaling/pathway_activity/phenotype_only/unknown",
"evidence_type": "in_vitro/animal/human/clinical/computational/curated_database/review/unknown",
"species": "human/mouse/rat/other/unknown",
"tissue_or_cell_context": "string or null", "disease_context": "string or null",
"evidence_strength": "strong/moderate/weak/insufficient",
"rationale": "1-2 sentence explanation", "confidence": 0.0-1.0}}"""

def classify_evidence(text: str, gene: str, drug: str) -> EvidenceClassification:
    if not text or not config.ANTHROPIC_API_KEY:
        return _empty()
    try:
        resp = requests.post(
            "https://api.anthropic.com/v1/messages",
            headers={"x-api-key": config.ANTHROPIC_API_KEY,
                     "anthropic-version": "2023-06-01",
                     "content-type": "application/json"},
            json={"model": config.LLM_MODEL, "max_tokens": config.LLM_MAX_TOKENS,
                  "system": SYSTEM_PROMPT,
                  "messages": [{"role": "user", "content": PROMPT_TEMPLATE.format(
                      gene=gene, drug=drug, text=text[:3000])}]},
            timeout=30
        )
        resp.raise_for_status()
        raw = resp.json()["content"][0]["text"]
        clean = re.sub(r"```(?:json)?|```", "", raw).strip()
        d = json.loads(clean)
        return EvidenceClassification(
            supports_drug_gene_relationship=bool(d.get("supports_drug_gene_relationship", False)),
            directness=d.get("directness", "unclear"),
            mechanism=d.get("mechanism", "unknown"),
            direction=d.get("direction", "unclear"),
            biological_level=d.get("biological_level", "unknown"),
            evidence_type=d.get("evidence_type", "unknown"),
            species=d.get("species", "unknown"),
            tissue_or_cell_context=d.get("tissue_or_cell_context"),
            disease_context=d.get("disease_context"),
            evidence_strength=d.get("evidence_strength", "insufficient"),
            rationale=d.get("rationale"),
            confidence=float(d.get("confidence", 0.0)),
            raw_llm_response=raw
        )
    except Exception as e:
        print(f"[classify_evidence] Error: {e}")
        return _empty()

def classify_evidence_batch(evidence_texts, gene, drug):
    results = []
    for et in evidence_texts:
        text = ((et.title or "") + ". " + (et.abstract or "")).strip()
        results.append(classify_evidence(text, gene, drug))
    return results

def _empty(raw=None):
    return EvidenceClassification(supports_drug_gene_relationship=False,
                                   evidence_strength="insufficient", raw_llm_response=raw)
