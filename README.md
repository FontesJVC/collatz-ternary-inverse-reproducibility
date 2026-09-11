# Computational Reproducibility for the Collatz Companion Papers

This repository contains computational verification scripts, adversarial
counterexample searches, execution logs, and reproducibility materials for two
companion manuscripts on the accelerated odd Collatz inverse map.

The computational material is a **separate falsification and reproducibility
layer**. It does not replace the analytic proofs in the manuscripts.

> **Version note.** The previously archived Zenodo release `v1.0.1`
> (DOI: `10.5281/zenodo.22715986`) is superseded for the final manuscripts by
> the corrected `v1.0.2` code on `main`. Version `v1.0.2` replaces one
> floating-point comparison in a convenience no-wrap predicate by an exact
> integer comparison and removes an organizational Paper 2 -> Paper 1 code
> dependency. The mathematical statements and analytic proofs are unchanged.

## Which files belong to which paper?

The repository is shared by both manuscripts, but the material is explicitly
separated:

- **Paper 1:** see [`paper1/`](paper1/README.md), together with the shared
  arithmetic/audit utilities in [`shared/`](shared/README.md).
- **Paper 2:** see [`paper2/`](paper2/README.md), together with the shared
  utilities and the deeper stress tests in [`deep_audit/`](deep_audit/README.md).

## Repository layout

```text
shared/       common arithmetic and cross-paper structural audit
paper1/       Paper 1-specific computational core and notes
paper2/       Paper 2-specific computational core and notes
deep_audit/   deeper falsification suite, logs, and results
tests/        smoke tests and adversarial examples
scripts/      Windows runners and Excel conversion helper
logs/         quick/full audit logs shared across the project
```

## Requirements

Python 3.10+ is recommended. The computational core uses only the Python
standard library.

## Quick start

```bash
python tests/run_smoke_tests.py
python shared/collatz_structural_audit.py --suite quick
python shared/collatz_structural_audit.py --suite full
python tests/search_counterexamples.py
```

For the deeper audit:

```bash
python deep_audit/deep_audit.py --preset deep
```

or, for a heavier run:

```bash
python deep_audit/deep_audit.py --preset overnight
```

On Windows, the scripts in `scripts/` provide double-clickable runners.

## Completed deep audit

The manuscript-associated deep run included, among other checks:

- state classification and q=0 graph regularity/connectivity through `h=4`;
- ninefold refinement through `h=3 -> h=4`;
- 250 sampled fixed source/family fibers at `h=4`, with all
  `3^7 = 2187` q-residue classes enumerated per sampled fiber;
- 50,000 random kappa-isometry checks;
- 10,000 exact inverse paths with tested depths up to 40;
- 485 target-window searches over 100 odd targets `n <= 199`;
- 546 every-depth searches on 12 hard targets;
- 236 below-threshold adversarial searches.

No counterexample was found in the above-threshold tests that were executed.
Passing these tests is finite computational evidence only and is not a proof.

## GitHub and Zenodo versioning

GitHub hosts the current development version. The corrected manuscript-associated
snapshot is prepared as `v1.0.2` and should be archived jointly for both
companion papers on Zenodo. After Zenodo mints the `v1.0.2` DOI, that DOI will
replace the superseded `v1.0.1` DOI in the final manuscripts and citation
metadata.

See [`RELEASE_NOTES_v1.0.2.md`](RELEASE_NOTES_v1.0.2.md) for the exact scope of
the correction.

## AI-use disclosure

Generative AI tools were used during development to assist with language
editing, mathematical exploration, organization of arguments, refinement of
notation, adversarial examination, computational code generation/revision, and
presentation materials. The computational experiments are used only as
separate falsification and reproducibility checks, not as substitutes for
analytic proofs.

## License

The software in this repository is released under the [MIT License](LICENSE).
