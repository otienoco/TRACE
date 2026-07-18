#!/bin/bash
DISEASE="MASLD"
echo "Starting MASLD external validation..."
echo "Started at: $(date)"

# Positive effect size = increased_gene_increases_risk
for GENE in ABCB11 ABCC2 ALDH2 CPN1 FLT1 MYH7B SCN2A VEGFA; do
    echo "================================================"
    echo "Running gene: $GENE (increased_gene_increases_risk)"
    echo "Time: $(date)"
    echo "================================================"
    python scripts/run_gene.py --gene $GENE --disease "$DISEASE" --risk_direction increased_gene_increases_risk
done

# Negative effect size = decreased_gene_increases_risk
for GENE in APOE FADS3 PPARG S1PR2; do
    echo "================================================"
    echo "Running gene: $GENE (decreased_gene_increases_risk)"
    echo "Time: $(date)"
    echo "================================================"
    python scripts/run_gene.py --gene $GENE --disease "$DISEASE" --risk_direction decreased_gene_increases_risk
done

echo "All genes complete!"
echo "Finished at: $(date)"
