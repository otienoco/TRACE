#!/bin/bash
DISEASE="T2D"
echo "Starting T2D validation batch run..."
echo "Started at: $(date)"

# Increased gene increases risk (need antagonists/inhibitors)
for GENE in ACE KCNJ11 TH CACNA1A HCN3 SCN3A MAPK3 BCL2 IKBKE TAP2; do
    echo "================================================"
    echo "Running gene: $GENE (increased_gene_increases_risk)"
    echo "Time: $(date)"
    echo "================================================"
    python scripts/run_gene.py --gene $GENE --disease "$DISEASE" \
        --risk_direction increased_gene_increases_risk
done

# Decreased gene increases risk (need agonists/activators)
for GENE in GCK OPRL1; do
    echo "================================================"
    echo "Running gene: $GENE (decreased_gene_increases_risk)"
    echo "Time: $(date)"
    echo "================================================"
    python scripts/run_gene.py --gene $GENE --disease "$DISEASE" \
        --risk_direction decreased_gene_increases_risk
done

echo "All genes complete!"
echo "Finished at: $(date)"
