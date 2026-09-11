# Deep computational falsification audit

This directory contains the deeper finite stress-test suite used primarily to
support the computational/reproducibility discussion in Paper 2.

Run:

```bash
python deep_audit/deep_audit.py --preset deep
```

The manuscript-associated completed run is stored in:

- `logs/deep_audit_deep.txt`
- `results/deep_audit_deep.csv`
- `results/deep_audit_charts.xlsx` (Excel convenience workbook)

The `deep` preset includes broad target-window comparisons, every-depth sweeps
on hard targets, random kappa-isometry checks, exact inverse-path stress tests,
and deliberate below-threshold false-positive searches.

These are finite falsification checks, not proofs.
