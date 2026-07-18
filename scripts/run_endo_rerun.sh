#!/bin/bash
DISEASE="endometriosis"
echo "Rerunning empty genes..."
echo "Started at: $(date)"

for GENE in AC005165.1 AC015726.1 AC021755.2 AC021755.3 AC118658.1 AL133284.1 AL929236.1 AP000487.1 NOL4L-DT NOP9 PGR PLCG1 PPP1R14B PPP4C PRRT2 PRRX1 PTPRO RABGGTA RIN3 RNF146 SKAP1 TCEA2 TCF19 TLCD3B TMEM185B TMEM219 WNT4; do
    echo "================================================"
    echo "Running: $GENE (decreased_gene_increases_risk)"
    echo "Time: $(date)"
    echo "================================================"
    python scripts/run_gene.py --gene $GENE --disease "$DISEASE" --risk_direction decreased_gene_increases_risk
done

for GENE in AC018521.6 AC064836.3 AC103952.1 AC104758.2 AC105935.1 AC130371.2 AP003774.2 LINC02456 LTB4R LTB4R2 MPPED2-AS1; do
    echo "================================================"
    echo "Running: $GENE (increased_gene_increases_risk)"
    echo "Time: $(date)"
    echo "================================================"
    python scripts/run_gene.py --gene $GENE --disease "$DISEASE" --risk_direction increased_gene_increases_risk
done

echo "Rerun complete!"
echo "Finished at: $(date)"
