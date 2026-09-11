# Paper 1 reproducibility map

This directory contains the computational core specific to:

**Finite Ternary Residual Geometry for the Accelerated Odd Collatz Inverse Map:
Affine Lifting, Recursive Signatures, and Minimal-Exponent Skeletons**

Primary file:

- `paper1_core.py` — minimal-q residual skeleton helpers, finite graph
  construction, degree checks, and strong-connectivity helpers.

Additional Paper 1 checks are implemented in:

- `../shared/collatz_structural_audit.py`
- `../tests/run_smoke_tests.py`

The quick/full logs in `../logs/` include Paper 1 structural checks such as
state counts, q=0 graph regularity/connectivity, and ninefold refinement.
