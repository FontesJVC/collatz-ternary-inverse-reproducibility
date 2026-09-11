# Shared computational material

This directory contains arithmetic utilities and the cross-paper structural
audit used by both companion manuscripts.

- `common.py` provides shared arithmetic helpers, including the elementary
  inverse-family base-exponent routine `b_t_from_unit` used by both papers.
- `collatz_structural_audit.py` contains the quick/full finite structural audit,
  target examples, low-precision false-positive demonstrations, and the
  finite-precision exactness comparisons used across the project.

The audit script deliberately combines tests relevant to both papers; the
paper-specific computational cores live in `paper1/` and `paper2/`. Paper 2 no
longer imports implementation code from the Paper 1 module.
