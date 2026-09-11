export const finrepOutput = {
  runStatus: {
    reportDate: '2026-08-31',
    entity: 'Demo Bank PLC',
    status: 'Approved',
    submission: 'Ready',
    summary: 'The COREP and FINREP production cycle completed successfully for the synthetic reporting date. The intake snapshot, mapping set, and calculations were validated against the approved controls. Remaining reconciliations were either within tolerance or explicitly approved by the designated owner.'
  },
  metrics: {
    controlsPassed: '8/8',
    breaksOpen: 0,
  },
  controls: [
    { id: 'CTRL-001', result: 'PASS', description: 'Source snapshot completeness validated for GL, sub-ledger, risk, and reference data.' },
    { id: 'CTRL-002', result: 'PASS', description: 'Taxonomy and mapping version approved for the active reporting instruction set.' },
    { id: 'CTRL-003', result: 'PASS', description: 'Data quality checks passed for nulls, duplicates, chronology, and dimensional scope.' },
    { id: 'CTRL-004', result: 'PASS', description: 'Calculation trace confirmed for capital, leverage, liquidity, and FINREP totals.' },
    { id: 'CTRL-005', result: 'PASS', description: 'Balance-to-risk and GL-to-subledger reconciliations stayed within tolerance.' },
    { id: 'CTRL-006', result: 'PASS', description: 'Lineage evidence pack was complete and hash-linked for material cells.' },
    { id: 'CTRL-007', result: 'PASS', description: 'Maker-checker approval path completed with recorded owner sign-off.' },
    { id: 'CTRL-008', result: 'PASS', description: 'Submission readiness gate confirmed with auditable evidence retained.' }
  ],
  reconciliation: [
    { name: 'GL vs. FINREP Assets', status: 'CLEAR', detail: 'Variance within tolerance and fully explained by non-reporting adjustments.' },
    { name: 'COREP own funds vs. equity', status: 'CLEAR', detail: 'Capital composition reconciled across regulatory and accounting dimensions.' },
    { name: 'Large exposure mapping', status: 'CLEAR', detail: 'Exposure population and aggregator logic aligned with approved taxonomy.' }
  ],
  lineages: [
    'GL ledger extract -> mapping layer -> COREP template cells',
    'Sub-ledger balances -> reconciliation engine -> FINREP statement totals',
    'Risk data -> capital and leverage calculations -> evidence bundle',
    'Approval decisions -> submission hash -> retained audit record'
  ],
  approvals: [
    { label: 'Data steward approval', value: 'Approved' },
    { label: 'Finance review', value: 'Approved' },
    { label: 'Submission release', value: 'Approved' }
  ]
};
