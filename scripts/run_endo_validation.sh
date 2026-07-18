#!/bin/bash

DISEASE="endometriosis"

echo "Starting endometriosis validation batch run..."
echo "Started at: $(date)"

echo "================================================"
echo "Running gene: FSHR (increased_gene_increases_risk)"
echo "Time: $(date)"
echo "================================================"
python scripts/run_gene.py --gene FSHR --disease "$DISEASE" --risk_direction increased_gene_increases_risk

echo "================================================"
echo "Running gene: PGR (decreased_gene_increases_risk)"
echo "Time: $(date)"
echo "================================================"
python scripts/run_gene.py --gene PGR --disease "$DISEASE" --risk_direction decreased_gene_increases_risk

echo "================================================"
echo "Running gene: PTGER4 (increased_gene_increases_risk)"
echo "Time: $(date)"
echo "================================================"
python scripts/run_gene.py --gene PTGER4 --disease "$DISEASE" --risk_direction increased_gene_increases_risk

echo "================================================"
echo "Running gene: CDKN2A (increased_gene_increases_risk)"
echo "Time: $(date)"
echo "================================================"
python scripts/run_gene.py --gene CDKN2A --disease "$DISEASE" --risk_direction increased_gene_increases_risk

echo "================================================"
echo "Running gene: KDR (decreased_gene_increases_risk)"
echo "Time: $(date)"
echo "================================================"
python scripts/run_gene.py --gene KDR --disease "$DISEASE" --risk_direction decreased_gene_increases_risk

echo "================================================"
echo "Running gene: GNRH1 (decreased_gene_increases_risk)"
echo "Time: $(date)"
echo "================================================"
python scripts/run_gene.py --gene GNRH1 --disease "$DISEASE" --risk_direction decreased_gene_increases_risk

echo ""
echo "All genes complete!"
echo "Finished at: $(date)"
