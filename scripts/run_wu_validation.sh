#!/bin/bash
DISEASE="hyperlipidemia"
echo "Starting Wu et al. 2022 validation..."
echo "Started at: $(date)"

echo "================================================"
echo "Running gene: PCSK9 (increased_gene_increases_risk)"
echo "================================================"
python scripts/run_gene.py --gene PCSK9 --disease "$DISEASE" --risk_direction increased_gene_increases_risk --use_local true

echo "================================================"
echo "Running gene: LDLR (decreased_gene_increases_risk)"
echo "================================================"
python scripts/run_gene.py --gene LDLR --disease "$DISEASE" --risk_direction decreased_gene_increases_risk --use_local true

echo "================================================"
echo "Running gene: HMGCR (increased_gene_increases_risk)"
echo "================================================"
python scripts/run_gene.py --gene HMGCR --disease "$DISEASE" --risk_direction increased_gene_increases_risk --use_local true

DISEASE="hypertension"
echo "================================================"
echo "Running gene: ACE (increased_gene_increases_risk)"
echo "================================================"
python scripts/run_gene.py --gene ACE --disease "$DISEASE" --risk_direction increased_gene_increases_risk --use_local true

echo "================================================"
echo "Running gene: ADRB1 (increased_gene_increases_risk)"
echo "================================================"
python scripts/run_gene.py --gene ADRB1 --disease "$DISEASE" --risk_direction increased_gene_increases_risk --use_local true

echo "All genes complete!"
echo "Finished at: $(date)"
