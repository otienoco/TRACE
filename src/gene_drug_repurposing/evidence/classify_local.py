"""
Local PubMedBERT classifier — replaces Claude API calls.
Runs on your server, free, fast, no API key needed.
"""
import os
import torch
from torch import nn
from transformers import AutoTokenizer, AutoModel
from ..schemas import EvidenceClassification

MODEL_DIR = "models/pubmedbert_drug_gene"

MECHANISM_LABELS = [
    "inhibitor", "antagonist", "agonist", "activator",
    "downregulator", "upregulator", "degrader",
    "binder_only", "modulator_unclear_direction", "unknown"
]

DIRECTION_LABELS = [
    "decreases_expression", "increases_expression",
    "decreases_activity", "increases_activity",
    "mixed", "unclear", "not_applicable"
]

class DrugGeneClassifier(nn.Module):
    def __init__(self, model_name, n_mech, n_dir):
        super().__init__()
        self.bert      = AutoModel.from_pretrained(model_name)
        hidden         = self.bert.config.hidden_size
        self.dropout   = nn.Dropout(0.1)
        self.head_rel  = nn.Linear(hidden, 2)
        self.head_mech = nn.Linear(hidden, n_mech)
        self.head_dir  = nn.Linear(hidden, n_dir)

    def forward(self, input_ids, attention_mask):
        out    = self.bert(input_ids=input_ids, attention_mask=attention_mask)
        pooled = self.dropout(out.last_hidden_state[:, 0, :])
        return self.head_rel(pooled), self.head_mech(pooled), self.head_dir(pooled)

_model     = None
_tokenizer = None
_device    = None

def _load_model():
    global _model, _tokenizer, _device
    if _model is not None:
        return
    best_model_path = os.path.join(MODEL_DIR, "best_model")
    state_path      = os.path.join(MODEL_DIR, "best_model_state.pt")
    if not os.path.exists(best_model_path):
        print(f"[classify_local] Model not found at {best_model_path}")
        return
    print(f"[classify_local] Loading local model...")
    _device    = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    _tokenizer = AutoTokenizer.from_pretrained(best_model_path)
    _model     = DrugGeneClassifier(best_model_path, len(MECHANISM_LABELS), len(DIRECTION_LABELS))
    _model.load_state_dict(torch.load(state_path, map_location=_device), strict=False)
    _model.to(_device)
    _model.eval()
    print(f"[classify_local] Model loaded on {_device}")

def classify_evidence_local(text: str, gene: str, drug: str) -> EvidenceClassification:
    _load_model()
    if _model is None or not text or not text.strip():
        return _empty()
    try:
        input_text = f"{gene} [SEP] {drug} [SEP] {text[:2000]}"
        encoding   = _tokenizer(
            input_text,
            max_length=512,
            padding="max_length",
            truncation=True,
            return_tensors="pt"
        )
        input_ids      = encoding["input_ids"].to(_device)
        attention_mask = encoding["attention_mask"].to(_device)

        with torch.no_grad():
            logits_rel, logits_mech, logits_dir = _model(input_ids, attention_mask)

        rel_prob   = torch.softmax(logits_rel,  dim=-1)[0]
        mech_prob  = torch.softmax(logits_mech, dim=-1)[0]
        dir_prob   = torch.softmax(logits_dir,  dim=-1)[0]

        supports   = rel_prob[1].item() > 0.5
        mechanism  = MECHANISM_LABELS[mech_prob.argmax().item()]
        direction  = DIRECTION_LABELS[dir_prob.argmax().item()]
        confidence = rel_prob[1].item()

        if confidence > 0.85:   strength = "strong"
        elif confidence > 0.65: strength = "moderate"
        elif confidence > 0.45: strength = "weak"
        else:                   strength = "insufficient"

        return EvidenceClassification(
            supports_drug_gene_relationship=supports,
            mechanism=mechanism,
            direction=direction,
            evidence_strength=strength,
            confidence=round(confidence, 3),
            rationale=f"Local model: {mechanism}/{direction} (conf={confidence:.2f})"
        )
    except Exception as e:
        print(f"[classify_local] Error: {e}")
        return _empty()

def classify_evidence_batch_local(evidence_texts, gene, drug):
    results = []
    for et in evidence_texts:
        text = ((et.title or "") + ". " + (et.abstract or "")).strip()
        results.append(classify_evidence_local(text, gene, drug))
    return results

def _empty():
    return EvidenceClassification(
        supports_drug_gene_relationship=False,
        evidence_strength="insufficient"
    )
