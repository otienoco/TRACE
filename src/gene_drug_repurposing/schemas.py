from dataclasses import dataclass, field
from typing import Optional

@dataclass
class GeneRecord:
    input_gene: str
    official_symbol: str
    gene_id: Optional[str] = None
    ensembl_id: Optional[str] = None
    uniprot_id: Optional[str] = None
    aliases: list = field(default_factory=list)
    normalization_source: str = "HGNC"
    normalized: bool = False
    def to_dict(self): return self.__dict__

@dataclass
class DrugRecord:
    drug_name: str
    normalized_drug_name: str
    brand_names: list = field(default_factory=list)
    rxnorm_id: Optional[str] = None
    pubchem_cid: Optional[str] = None
    fda_approved_us: Optional[bool] = None
    approval_source: Optional[str] = None
    approval_confidence: str = "unknown"
    def to_dict(self): return self.__dict__

@dataclass
class DrugGeneCandidate:
    gene: str
    drug: str
    source_database: str
    interaction_type: Optional[str] = None
    evidence_level: Optional[str] = None
    pmids: list = field(default_factory=list)
    source_url: Optional[str] = None
    raw_annotation: Optional[str] = None
    def to_dict(self): return self.__dict__

@dataclass
class EvidenceText:
    pmid: Optional[str]
    title: Optional[str]
    abstract: Optional[str]
    journal: Optional[str] = None
    year: Optional[int] = None
    query_used: Optional[str] = None
    gene_mentioned: bool = False
    drug_mentioned: bool = False
    source: str = "PubMed"
    def to_dict(self): return self.__dict__

@dataclass
class EvidenceClassification:
    supports_drug_gene_relationship: bool
    directness: str = "unclear"
    mechanism: str = "unknown"
    direction: str = "unclear"
    biological_level: str = "unknown"
    evidence_type: str = "unknown"
    species: str = "unknown"
    tissue_or_cell_context: Optional[str] = None
    disease_context: Optional[str] = None
    evidence_strength: str = "insufficient"
    rationale: Optional[str] = None
    confidence: float = 0.0
    raw_llm_response: Optional[str] = None
    def to_dict(self): return self.__dict__

@dataclass
class DrugGenePair:
    gene: str
    drug: str
    gene_record: Optional[object] = None
    drug_record: Optional[object] = None
    source_databases: list = field(default_factory=list)
    raw_candidates: list = field(default_factory=list)
    evidence_texts: list = field(default_factory=list)
    evidence_classifications: list = field(default_factory=list)
    consensus_mechanism: str = "unknown"
    consensus_direction: str = "unclear"
    consensus_evidence_strength: str = "insufficient"
    fda_approved: Optional[bool] = None
    therapeutic_classification: str = "drug_gene_pair_only_no_therapeutic_interpretation"
    priority_score: int = 0
    priority_tier: str = "exclude_manual_review"
    rationale: str = ""
    manual_review_flag: bool = False
    supporting_pmids: list = field(default_factory=list)
    def to_dict(self):
        d = self.__dict__.copy()
        d["gene_record"] = self.gene_record.to_dict() if self.gene_record else None
        d["drug_record"] = self.drug_record.to_dict() if self.drug_record else None
        d["raw_candidates"] = [c.to_dict() for c in self.raw_candidates]
        d["evidence_texts"] = [e.to_dict() for e in self.evidence_texts]
        d["evidence_classifications"] = [c.to_dict() for c in self.evidence_classifications]
        return d

@dataclass
class PipelineInput:
    gene: str
    disease: Optional[str] = None
    risk_direction: str = "unknown"
    species: str = "human"
    fda_only: bool = True
    minimum_evidence_level: str = "Stage 4"
    include_safety_drugs: bool = True
    def to_dict(self): return self.__dict__
