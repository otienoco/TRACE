import os
from dotenv import load_dotenv
load_dotenv()

ANTHROPIC_API_KEY   = os.getenv("ANTHROPIC_API_KEY", "")
NCBI_API_KEY        = os.getenv("NCBI_API_KEY", "")
PUBMED_BASE_URL     = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils"
PUBMED_MAX_RESULTS  = 7
DGIDB_GRAPHQL_URL   = "https://dgidb.org/api/graphql"
OPENTARGETS_API_URL = "https://api.platform.opentargets.org/api/v4/graphql"
OPENFDA_BASE_URL    = "https://api.fda.gov/drug"
RXNORM_BASE_URL     = "https://rxnav.nlm.nih.gov/REST"
HGNC_BASE_URL       = "https://rest.genenames.org"

SCORE_FDA_APPROVED         = 3
SCORE_DIRECT_TARGET        = 3
SCORE_CLEAR_DIRECTIONALITY = 3
SCORE_MECHANISM_KNOWN      = 2
SCORE_HUMAN_EVIDENCE       = 2
SCORE_DISEASE_RELEVANT     = 2
SCORE_PER_DATABASE         = 1
SCORE_MAX_DATABASE_BONUS   = 4
SCORE_PER_PMID             = 1
SCORE_MAX_PMID_BONUS       = 5
SCORE_STAGE4_EVIDENCE      = 3
SCORE_CONFLICTING_EVIDENCE = -3
SCORE_UNCLEAR_MECHANISM    = -2
SCORE_NON_FDA              = -5
PRIORITY_HIGH_THRESHOLD    = 12
PRIORITY_MEDIUM_THRESHOLD  = 6

LLM_MODEL      = "claude-sonnet-4-5"
LLM_MAX_TOKENS = 1000
OUTPUT_DIR     = "results"

CTD_BASE_URL       = "https://ctdbase.org/tools/batchQuery.go"
PHAROS_GRAPHQL_URL = "https://pharos-api.ncats.io/graphql"
