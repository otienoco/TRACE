# TRACE: TWAS-driven Repurposing through AI-assisted Curation of Evidence

TRACE is a gene-agnostic computational pipeline that automates the translation of transcriptome-wide association study (TWAS) findings into directionally informed drug repurposing hypotheses. Given a gene symbol and TWAS effect-size direction, TRACE retrieves FDA-approved drug candidates from four interaction databases, collects PubMed evidence, and uses a fine-tuned BiomedBERT classifier to determine whether each drug acts in a therapeutically concordant direction.

## Citation

If you use TRACE in your research, please cite:

> Otieno CO, Seagle HM, Akerele AT, Jaworski J, Guare L, Setia-Verma S, Velez Edwards DR, Edwards TL.
> TRACE: A fine-tuned biomedical language model for directionally informed drug repurposing
> from transcriptome-wide association studies. 2026. Preprint.

## Requirements

- Python 3.11
- Conda (recommended)

## Installation

```bash
git clone https://github.com/otienoco/TRACE.git
cd TRACE
conda create -n trace python=3.11
conda activate trace
pip install -r requirements.txt
```

## Data Setup

TRACE requires one external data file from the Comparative Toxicogenomics Database (CTD):

1. Download directly using this command:
```bash
mkdir -p data/raw
wget -O data/raw/CTD_chem_gene_ixns.tsv.gz "https://ctdbase.org/reports/CTD_chem_gene_ixns.tsv.gz"
```

Or manually download from https://ctdbase.org/downloads/ — look for **Chemical-gene interactions** and place the file at `data/raw/CTD_chem_gene_ixns.tsv.gz`

## Installation

```bash
git clone https://github.com/otienoco/TRACE.git
cd TRACE
conda create -n trace python=3.11
conda activate trace
pip install .
```

## Verify Installation

Run this to confirm everything is working before running your full gene list:

```bash
python scripts/run_gene.py \
  --gene PTGER4 \
  --disease "endometriosis" \
  --risk_direction increased_gene_increases_risk \
  --use_local true
```

This should complete in 10-20 minutes and create output files in `results/endometriosis/`. The first run will automatically download the model weights from Hugging Face (~2.6GB) so allow extra time.

## Model Weights

The fine-tuned BiomedBERT classifier weights are hosted on Hugging Face and will be **downloaded automatically on first run**. No manual setup needed.

Model repository: https://huggingface.co/otienoco/TRACE-classifier

**Note for HPC users:** If running on a cluster where compute nodes do not have internet access, download the model weights once on a login node that has internet access by running `python -c "from huggingface_hub import snapshot_download; snapshot_download(repo_id='otienoco/TRACE-classifier', local_dir='models/pubmedbert_drug_gene')"` before submitting jobs.

## API Keys

TRACE uses the NCBI E-utilities API for PubMed retrieval. A free NCBI API key increases your rate limit and is recommended for large gene lists.

Create a `.env` file in the project root:

```bash
ANTHROPIC_API_KEY=   # only needed if using --use_local false
NCBI_API_KEY=your_ncbi_api_key_here
```

Get a free NCBI API key at: https://www.ncbi.nlm.nih.gov/account/

## Usage

### Single gene
```bash
python scripts/run_gene.py \
  --gene PTGER4 \
  --disease "endometriosis" \
  --risk_direction increased_gene_increases_risk \
  --use_local true
```

### Batch run (multiple genes)
Risk directions must be supplied by the user based on the sign of the effect estimate from their TWAS or S-PrediXcan output. A positive effect estimate corresponds to increased_gene_increases_risk and a negative effect estimate corresponds to decreased_gene_increases_risk.

```bash
# TRACE batch run
# Replace gene symbols below with your own gene lists
# grouped by TWAS effect direction

DISEASE="hypertension"  # change to your disease name

# GROUP 1: Genes where INCREASED expression increases disease risk
# positive beta/effect size from S-PrediXcan or TWAS
for GENE in GENE_A GENE_B GENE_C; do
    python scripts/run_gene.py \
      --gene $GENE \
      --disease "$DISEASE" \
      --risk_direction increased_gene_increases_risk \
      --use_local true
done

# GROUP 2: Genes where DECREASED expression increases disease risk
# negative beta/effect size from S-PrediXcan or TWAS
for GENE in GENE_D GENE_E GENE_F; do
    python scripts/run_gene.py \
      --gene $GENE \
      --disease "$DISEASE" \
      --risk_direction decreased_gene_increases_risk \
      --use_local true
done
```

### Risk direction options
- `increased_gene_increases_risk` — positive beta from TWAS/S-PrediXcan; pipeline looks for inhibitors/downregulators
- `decreased_gene_increases_risk` — negative beta from TWAS/S-PrediXcan; pipeline looks for activators/upregulators 

### Output

Results are written to `results/` as CSV, JSON, and Markdown, with pairs classified as:
- `candidate_therapeutic_pair` — drug direction is concordant with therapeutic need
- `potential_safety_concern` — drug direction opposes therapeutic need
- `unclear_direction_manual_review` — relationship documented but direction unclear
- `drug_gene_pair_only` — interaction confirmed but no risk direction assigned

## Validation

TRACE was validated against three independent disease settings:
- Endometriosis (internal gold standard, 43 pairs): **90.7% recall**
- MASLD (Seagle et al. 2025, PMID:40780050, 34 pairs): **88.2% recall**
- Type 2 diabetes (Shuey et al. 2023, PMID:37399599, 20 pairs): **92.9% adjusted recall**

## License

MIT License

## Contact

Christopher O. Otieno — christopher.otieno@vanderbilt.edu
