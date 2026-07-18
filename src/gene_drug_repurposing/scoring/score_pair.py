from .. import config

def aggregate_evidence(pair):
    supported = [ec for ec in pair.evidence_classifications if ec.supports_drug_gene_relationship]
    if not supported:
        pair.consensus_mechanism = "unknown"
        pair.consensus_direction = "unclear"
        pair.consensus_evidence_strength = "insufficient"
        return pair
    def majority(items): 
        counts = {}
        for i in items: counts[i] = counts.get(i, 0) + 1
        return max(counts, key=counts.get)
    pair.consensus_mechanism = majority([ec.mechanism for ec in supported])
    pair.consensus_direction = majority([ec.direction for ec in supported])
    rank = {"strong":4,"moderate":3,"weak":2,"insufficient":1}
    pair.consensus_evidence_strength = max(supported, key=lambda ec: rank.get(ec.evidence_strength,0)).evidence_strength
    pair.supporting_pmids = list({et.pmid for et in pair.evidence_texts if et.pmid and et.gene_mentioned and et.drug_mentioned})
    return pair

def score_pair(pair):
    score = 0
    reasons = []
    if pair.fda_approved is True:
        score += config.SCORE_FDA_APPROVED; reasons.append("FDA-approved")
    elif pair.fda_approved is False:
        score += config.SCORE_NON_FDA; reasons.append("Not FDA-approved (penalized)")
    if any(ec.directness == "direct" and ec.supports_drug_gene_relationship for ec in pair.evidence_classifications):
        score += config.SCORE_DIRECT_TARGET; reasons.append("Direct target engagement")
    if pair.consensus_direction not in ("unclear","mixed","unknown","not_applicable"):
        score += config.SCORE_CLEAR_DIRECTIONALITY; reasons.append(f"Clear direction: {pair.consensus_direction}")
    if pair.consensus_mechanism not in ("unknown","modulator_unclear_direction"):
        score += config.SCORE_MECHANISM_KNOWN; reasons.append(f"Known mechanism: {pair.consensus_mechanism}")
    else:
        score += config.SCORE_UNCLEAR_MECHANISM; reasons.append("Unclear mechanism (penalized)")
    if any(ec.species == "human" and ec.supports_drug_gene_relationship for ec in pair.evidence_classifications):
        score += config.SCORE_HUMAN_EVIDENCE; reasons.append("Human evidence")
    if any(ec.disease_context and ec.supports_drug_gene_relationship for ec in pair.evidence_classifications):
        score += config.SCORE_DISEASE_RELEVANT; reasons.append("Disease-relevant evidence")
    db_bonus = min(len(pair.source_databases), config.SCORE_MAX_DATABASE_BONUS)
    score += db_bonus
    if db_bonus: reasons.append(f"{len(pair.source_databases)} database(s)")
    pmid_bonus = min(len(pair.supporting_pmids), config.SCORE_MAX_PMID_BONUS)
    score += pmid_bonus
    if pmid_bonus: reasons.append(f"{len(pair.supporting_pmids)} PMID(s)")
    directions = set(ec.direction for ec in pair.evidence_classifications
                     if ec.supports_drug_gene_relationship and ec.direction not in ("unclear","not_applicable","unknown"))
    if len(directions) > 1:
        score += config.SCORE_CONFLICTING_EVIDENCE; reasons.append("Conflicting evidence (penalized)")
    if score >= config.PRIORITY_HIGH_THRESHOLD: tier = "high"
    elif score >= config.PRIORITY_MEDIUM_THRESHOLD: tier = "medium"
    elif score > 0: tier = "low"
    else: tier = "exclude_manual_review"
    if pair.fda_approved is False: tier = "exclude_manual_review"
    pair.priority_score = score
    pair.priority_tier = tier
    pair.rationale = ". ".join(reasons) + "."
    return pair
