# Paper 2 reproducibility map

This directory contains the computational core specific to:

**Ternary Edge Codes and Exact Path Realization for the Accelerated Odd Collatz
Inverse Map: Layered Residual Systems, 3-Adic Edge Geometry, and Archimedean
Exactness**

Primary file:

- `paper2_core.py` — full edge-code helpers, kappa coding/isometry utilities,
  layered moduli, no-wrap threshold helpers, and exact-path controls.

Additional Paper 2 checks are implemented in:

- `../shared/collatz_structural_audit.py`
- `../tests/search_counterexamples.py`
- `../deep_audit/deep_audit.py`

The deep audit and its manuscript-associated output are kept under
`../deep_audit/`.
