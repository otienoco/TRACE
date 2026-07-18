INHIBITORY_MECHANISMS = {
    "inhibitor", "antagonist", "downregulator", "degrader", "binder_only"
}
ACTIVATING_MECHANISMS = {
    "agonist", "activator", "upregulator"
}
DECREASING_DIRECTIONS = {"decreases_expression", "decreases_activity"}
INCREASING_DIRECTIONS = {"increases_expression", "increases_activity"}

def classify_therapeutic_direction(disease_risk_direction, consensus_mechanism,
                                   consensus_direction, drug_name=None):
    if disease_risk_direction == "unknown":
        return "drug_gene_pair_only_no_therapeutic_interpretation", False

    effect = _resolve_effect(consensus_mechanism, consensus_direction)

    if effect == "unclear":
        return "unclear_direction_manual_review", True

    if disease_risk_direction == "increased_gene_increases_risk":
        if effect == "inhibitory": return "candidate_therapeutic_pair", False
        if effect == "activating": return "potential_safety_concern", False
    elif disease_risk_direction == "decreased_gene_increases_risk":
        if effect == "activating": return "candidate_therapeutic_pair", False
        if effect == "inhibitory": return "potential_safety_concern", False

    return "unclear_direction_manual_review", True

def _resolve_effect(mechanism, direction):
    # Direction is strongest signal — comes from actual abstract evidence
    if direction in DECREASING_DIRECTIONS: return "inhibitory"
    if direction in INCREASING_DIRECTIONS: return "activating"
    # Fall back to mechanism from abstract evidence
    if mechanism in INHIBITORY_MECHANISMS: return "inhibitory"
    if mechanism in ACTIVATING_MECHANISMS: return "activating"
    # modulator with unclear direction — genuinely unclear, needs manual review
    return "unclear"

def normalize_mechanism_string(raw):
    if not raw: return "unknown"
    r = raw.lower()
    for k, v in [
        ("inhibitor","inhibitor"),("inhibits","inhibitor"),
        ("suppress","inhibitor"),("blocker","inhibitor"),
        ("antagonist","antagonist"),("degrader","degrader"),
        ("downregulat","downregulator"),("agonist","agonist"),
        ("activator","activator"),("upregulat","upregulator"),
        ("inducer","upregulator"),("binder","binder_only"),
        ("modulator","modulator_unclear_direction")
    ]:
        if k in r: return v
    return "unknown"
