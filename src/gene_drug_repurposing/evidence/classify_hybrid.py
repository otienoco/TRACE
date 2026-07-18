"""
Hybrid classifier:
- Uses Claude API for primary classification (best labels for training)
- Simultaneously runs local model for comparison
- Logs disagreements for manual review (most valuable training examples)
- Automatically adds high-confidence examples to training queue
"""
import os
import json
import csv
from datetime import datetime
from .classify_llm import classify_evidence, _empty as llm_empty
from .classify_local import classify_evidence_local, _load_model
from ..schemas import EvidenceClassification

DISAGREEMENT_LOG = "data/annotations/disagreements.csv"
TRAINING_QUEUE   = "data/annotations/training_queue.jsonl"

os.makedirs("data/annotations", exist_ok=True)

def classify_evidence_hybrid(text: str, gene: str, drug: str,
                              use_local: bool = False) -> EvidenceClassification:
    """
    Hybrid classification:
    - If use_local=True: use local model only (free, fast)
    - If use_local=False: use Claude API + local model comparison
    
    Always logs disagreements for future training.
    """
    # Get Claude API result (primary)
    if not use_local:
        claude_result = classify_evidence(text, gene, drug)
    else:
        claude_result = None

    # Get local model result (always run for comparison/training)
    local_result = classify_evidence_local(text, gene, drug)

    # If using local model only, return it directly
    if use_local or claude_result is None:
        return local_result

    # Compare results and log disagreements
    _compare_and_log(text, gene, drug, claude_result, local_result)

    # Return Claude result as primary (more reliable)
    return claude_result


def classify_evidence_batch_hybrid(evidence_texts, gene, drug, use_local=False):
    """Classify a batch of abstracts using hybrid approach."""
    results = []
    for et in evidence_texts:
        text = ((et.title or "") + ". " + (et.abstract or "")).strip()
        results.append(classify_evidence_hybrid(text, gene, drug, use_local=use_local))
    return results


def _compare_and_log(text, gene, drug, claude_result, local_result):
    """Log disagreements between Claude and local model for training."""
    mech_agree = claude_result.mechanism == local_result.mechanism
    dir_agree  = claude_result.direction  == local_result.direction
    rel_agree  = claude_result.supports_drug_gene_relationship == \
                 local_result.supports_drug_gene_relationship

    # Log every comparison to training queue
    entry = {
        "timestamp":     datetime.now().isoformat(),
        "gene":          gene,
        "drug":          drug,
        "text":          text[:500],
        "claude_rel":    claude_result.supports_drug_gene_relationship,
        "claude_mech":   claude_result.mechanism,
        "claude_dir":    claude_result.direction,
        "claude_conf":   claude_result.confidence,
        "local_rel":     local_result.supports_drug_gene_relationship,
        "local_mech":    local_result.mechanism,
        "local_dir":     local_result.direction,
        "local_conf":    local_result.confidence,
        "mech_agree":    mech_agree,
        "dir_agree":     dir_agree,
        "rel_agree":     rel_agree,
        "is_disagreement": not (mech_agree and dir_agree and rel_agree),
    }

    with open(TRAINING_QUEUE, "a") as f:
        f.write(json.dumps(entry) + "\n")

    # Log disagreements separately for easy manual review
    if not (mech_agree and dir_agree and rel_agree):
        write_header = not os.path.exists(DISAGREEMENT_LOG)
        with open(DISAGREEMENT_LOG, "a", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=entry.keys())
            if write_header:
                writer.writeheader()
            writer.writerow(entry)
