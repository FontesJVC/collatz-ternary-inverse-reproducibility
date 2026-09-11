# Release v1.0.2 — exact-arithmetic correction

This release corrects a numerical implementation defect identified during an
independent reproducibility review of the supplementary code.

## Corrected

- `paper2/paper2_core.py::no_wrap_bound_holds` now evaluates
  `3^(2h) > (3/2)(n+1)^2` using exact integer arithmetic:
  `2*3^(2h) > 3*(n+1)^2`.
- A regression test was added for the explicit case
  `h=35`, `n=40850585511864587`, where the previous floating-point
  implementation returned the wrong Boolean value.

## Refactored

- The elementary helper `b_t_from_unit` was moved to `shared/common.py`.
  `paper2_core.py` therefore no longer imports code from `paper1_core.py`.
  This is an organizational refactor only and does not change the mathematics.

## Scope of the correction

The corrected function was a convenience predicate. The manuscript theorem
itself uses exact arithmetic, and the main horizon/search routines already used
integer or rational comparisons. The previously reported deep-audit counts are
therefore not invalidated by this fix.

## Verification

- smoke tests pass after the correction;
- the floating-point regression case is now tested explicitly.

The computational material remains finite falsification/reproducibility work
and is not a substitute for the analytic proofs in the companion manuscripts.
