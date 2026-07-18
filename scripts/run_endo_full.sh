#!/bin/bash
DISEASE="endometriosis"
echo "Starting full endometriosis gene batch run..."
echo "Started at: $(date)"

for GENE in AC018521.6 AC064836.3 AC103952.1 AC104758.2 AC105935.1 AC130371.2 AKAP10 AP003774.2 ASPHD1 ASTN2-AS1 ATXN7L2 BAZ2A BMF CALCRL CDKN2A CTSF DTD1 FAM71E2 FSHR GRB14 H2AFY2 KCNE4 KCTD13 LINC00652 LINC02456 MAFF MIRLET7BHG MPPED2-AS1 NACA NPEPL1 NSRP1 NUDT3 PRIM1 PTGER4 RBBP9 RCVRN RIT1 RPS20 SEC61A1 SMIM26 STX16 SYNE1 TBC1D2B TNFSF12 TSHZ3 VEZT WASHC3 YPEL3 ZHX3; do
    echo "================================================"
    echo "Running gene: $GENE (increased_gene_increases_risk)"
    echo "Time: $(date)"
    echo "================================================"
    python scripts/run_gene.py --gene $GENE --disease "$DISEASE" --risk_direction increased_gene_increases_risk --use_local true
done

for GENE in AC005165.1 AC015726.1 AC021755.2 AC021755.3 AC118658.1 ADK AL133284.1 AL929236.1 AP000487.1 ATF7IP BHLHE41 CACNA2D2 CCDC88B DOC2A DZIP1 EEFSEC EMILIN3 ERI1 GDAP1 GNRH1 HEMK1 INKA1 INO80E KDR LTB4R LTB4R2 NOL4L-DT NOP9 PGR PLCG1 PPP1R14B PPP4C PRRT2 PRRX1 PTPRO RABGGTA RIN3 RNF146 SKAP1 TCEA2 TCF19 TLCD3B TMEM185B TMEM219 WNT4; do
    echo "================================================"
    echo "Running gene: $GENE (decreased_gene_increases_risk)"
    echo "Time: $(date)"
    echo "================================================"
    python scripts/run_gene.py --gene $GENE --disease "$DISEASE" --risk_direction decreased_gene_increases_risk --use_local true
done

echo "All genes complete!"
echo "Finished at: $(date)"
