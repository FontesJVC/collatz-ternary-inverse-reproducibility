# Shared computational material

This directory contains arithmetic utilities and the cross-paper structural
audit used by both companion manuscripts.

- `common.py` provides shared arithmetic helpers.
- `collatz_structural_audit.py` contains the quick/full finite structural audit,
  target examples, low-precision false-positive demonstrations, and the
  finite-precision exactness comparisons used across the project.

The audit script deliberately combines tests relevant to both papers; the
paper-specific computational cores live in `paper1/` and `paper2/`.
