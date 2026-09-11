#!/usr/bin/env python3
"""
deep_audit.py

A deeper computational falsification suite for the two Collatz companion papers.

This program does NOT prove any theorem.  It deliberately pushes the finite
computational checks well beyond the small examples used in the manuscripts.

The suite has three presets:

    validation  - short run used to validate the script itself
    deep        - substantial desktop run
    overnight   - much heavier run intended for several hours / overnight use

Outputs:
    logs/deep_audit_<preset>.txt
    results/deep_audit_<preset>.csv

The most important test is the finite-precision exactness comparison:
for each target n and tested depth d, the target-pruned layered residual search
at h=h*(n) is compared against the direct reduced odd Collatz depth.
"""

from __future__ import annotations

import argparse
import csv
import random
import sys
import time
from pathlib import Path
from typing import Iterable, List, Tuple

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
sys.path.insert(0, str(ROOT))

from shared import collatz_structural_audit as c
from paper2.paper2_core import xi_y
from shared.common import v3

for _stream in (sys.stdout, sys.stderr):
    try:
        _stream.reconfigure(encoding="utf-8", errors="replace")
    except (AttributeError, ValueError):
        pass


def banner(title: str) -> None:
    print("\n" + "=" * 88)
    print(title)
    print("=" * 88)


def timed(label: str):
    class Timer:
        def __enter__(self):
            print(f"\n--- {label} ---")
            self.t0 = time.perf_counter()
            return self
        def __exit__(self, exc_type, exc, tb):
            dt = time.perf_counter() - self.t0
            print(f"--- completed in {dt:.3f} s ---")
    return Timer()


def sampled_full_fibers(h: int, samples: int, seed: int = 20260911) -> None:
    """
    Sample full q-bar fibers at a higher horizon than the exhaustive base suite.

    For every sampled (r,k,t), enumerate the COMPLETE q-bar range
        q = 0,...,3^(2h-1)-1
    and verify that the image is exactly the residue fiber x == t (mod 3).
    """
    rng = random.Random(seed + h)
    M = 3 ** (2 * h)
    Q = 3 ** (2 * h - 1)
    units = c.units_mod_3pow(2 * h)
    expected = {
        t: {x for x in range(M) if x % 3 == t}
        for t in c.D
    }
    for i in range(samples):
        r = rng.choice(units)
        k = rng.choice(c.D)
        t = rng.choice(c.D)
        vals = {c.phi_full(h, r, k, t, q) for q in range(Q)}
        if vals != expected[t]:
            raise AssertionError(
                f"Sampled full-fiber failure: h={h}, sample={i}, r={r}, k={k}, t={t}"
            )
    print(
        f"  h={h}: {samples} sampled fibers passed; "
        f"each fiber exhaustively enumerated over {Q} q-bar values"
    )


def random_kappa_isometry(trials: int, max_y: int, max_kappa: int, seed: int = 99117) -> None:
    """Random stress test of v3(Xi_y(a)-Xi_y(b)) = v3(a-b)."""
    rng = random.Random(seed)
    done = 0
    while done < trials:
        y = rng.randrange(1, max_y + 1, 2)
        if y % 3 == 0:
            continue
        a = rng.randrange(0, max_kappa + 1)
        b = rng.randrange(0, max_kappa + 1)
        if a == b:
            continue
        lhs = v3(xi_y(y, a) - xi_y(y, b))
        rhs = v3(a - b)
        if lhs != rhs:
            raise AssertionError(
                f"Kappa-isometry failure: y={y}, a={a}, b={b}, lhs={lhs}, rhs={rhs}"
            )
        done += 1
    print(f"  {done} random kappa pairs passed")


def deep_exact_path_stress(trials: int, max_depth: int, max_q: int, seed: int = 41027) -> None:
    """
    Stress finite realization, C_h(w), fixed-h projection, and the Archimedean
    envelope on exact inverse paths much deeper than the base random tests.
    """
    rng = random.Random(seed)
    max_seen_depth = 0
    max_seen_bits = 0

    for trial in range(1, trials + 1):
        h = rng.randint(1, 5)
        d = rng.randint(1, max_depth)
        max_seen_depth = max(max_seen_depth, d)

        while True:
            y0 = rng.randrange(1, 1000, 2)
            if y0 % 3:
                break

        labels = [(rng.choice(c.INTERIOR_T), rng.randint(0, max_q)) for _ in range(d)]
        steps = c.build_exact_inverse_path(y0, labels)
        c.fixed_h_path_data(h, steps)

        terminal = steps[-1].y_next
        exps = [s.b for s in steps]
        C = c.C_h_from_path(h, terminal % (3 ** (2 * h)), exps)
        mod = 3 ** (2 * h + d)

        if y0 % mod != C:
            raise AssertionError(
                f"C_h failure in deep path stress: trial={trial}, h={h}, d={d}"
            )

        ys = [y0] + [s.y_next for s in steps]
        n = ys[-1]
        max_seen_bits = max(max_seen_bits, max(y.bit_length() for y in ys))

        for j, y in enumerate(ys):
            if y > c.U(n, d, j):
                raise AssertionError(
                    f"Archimedean envelope failure: trial={trial}, d={d}, j={j}"
                )

        for j, st in enumerate(steps):
            if (1 << st.b) > c.L_bound(n, d, j):
                raise AssertionError(
                    f"Exponent envelope failure: trial={trial}, d={d}, j={j}"
                )

    print(
        f"  {trials} exact inverse paths passed; "
        f"max tested depth={max_seen_depth}, max integer bit-length={max_seen_bits}"
    )


def direct_depth(n: int) -> int | None:
    result = c.direct_reduced_depth(n, max_steps=100000)
    return None if result is None else result[0]


def test_one_target_depth(n: int, d: int, state_cap: int) -> Tuple[bool, int, float]:
    hs = c.h_star(n)
    true_d = direct_depth(n)
    t0 = time.perf_counter()
    res = c.layered_pruned_search(n, d, hs, state_cap=state_cap)
    elapsed = time.perf_counter() - t0
    expected = (true_d == d)
    if res.found != expected:
        raise AssertionError(
            f"Finite-precision exactness mismatch: n={n}, h*={hs}, d={d}, "
            f"residual={res.found}, direct_depth={true_d}"
        )
    return res.found, max(res.states_per_layer), elapsed


def target_window_sweep(
    max_target: int,
    radius: int,
    state_cap: int,
    writer: csv.writer,
) -> None:
    """
    Broad target sweep. For every odd n <= max_target, test the exact direct
    depth and nearby depths +/- radius.
    """
    total = 0
    reached = 0
    largest_depth = 0
    largest_states = 0
    slowest = (0.0, None, None)

    for n in range(1, max_target + 1, 2):
        td = direct_depth(n)
        if td is None:
            continue
        reached += 1
        largest_depth = max(largest_depth, td)
        if td == 0:
            continue

        depths = sorted({d for d in range(td - radius, td + radius + 1) if d >= 1})
        for d in depths:
            found, max_states, elapsed = test_one_target_depth(n, d, state_cap)
            writer.writerow([
                "window", n, c.h_star(n), td, d, found, max_states, f"{elapsed:.6f}"
            ])
            total += 1
            largest_states = max(largest_states, max_states)
            if elapsed > slowest[0]:
                slowest = (elapsed, n, d)

        if n % 25 == 1:
            print(
                f"  progress: n={n}/{max_target}, tests={total}, "
                f"largest direct depth={largest_depth}"
            )

    print(
        f"  broad window sweep passed: {total} residual searches over "
        f"{reached} odd targets; largest direct depth={largest_depth}; "
        f"largest layer={largest_states}; "
        f"slowest={slowest[0]:.3f}s at n={slowest[1]}, d={slowest[2]}"
    )


def hardest_targets(limit: int, top_k: int) -> List[Tuple[int, int]]:
    vals = []
    for n in range(3, limit + 1, 2):
        td = direct_depth(n)
        if td is not None:
            vals.append((td, n))
    vals.sort(reverse=True)
    return [(n, d) for d, n in vals[:top_k]]


def all_depth_sweep_on_hard_targets(
    limit: int,
    top_k: int,
    extra_depth: int,
    depth_cap: int,
    state_cap: int,
    writer: csv.writer,
) -> None:
    """
    For the hardest small targets, test EVERY depth from 1 through
    min(true_depth + extra_depth, depth_cap).
    """
    hard = hardest_targets(limit, top_k)
    print("  selected hard targets:", hard)

    total = 0
    for n, td in hard:
        dmax = min(td + extra_depth, depth_cap)
        print(f"  n={n}, direct depth={td}, testing all d=1..{dmax}")
        for d in range(1, dmax + 1):
            found, max_states, elapsed = test_one_target_depth(n, d, state_cap)
            writer.writerow([
                "all-depth", n, c.h_star(n), td, d, found, max_states, f"{elapsed:.6f}"
            ])
            total += 1
    print(f"  all-depth hard-target sweep passed: {total} residual searches")


def low_precision_adversarial_scan(
    max_target: int,
    radius: int,
    state_cap: int,
    writer: csv.writer,
) -> None:
    """
    Deliberately use h=h*(n)-1 when possible and look for surviving residual
    paths that are not exact integer paths.  These are EXPECTED below threshold.
    """
    false_positives = 0
    tested = 0
    examples = []

    for n in range(3, max_target + 1, 2):
        hs = c.h_star(n)
        if hs <= 1:
            continue
        hlow = hs - 1
        td = direct_depth(n)
        if td is None or td == 0:
            continue

        depths = sorted({d for d in range(max(1, td - radius), td + radius + 1)})
        for d in depths:
            t0 = time.perf_counter()
            res = c.layered_pruned_search(n, d, hlow, state_cap=state_cap)
            elapsed = time.perf_counter() - t0
            tested += 1
            exact = False
            if res.found:
                ys = c.exact_integers_from_layer_path(res)
                exact = bool(ys) and ys[-1] == n
                if not exact:
                    false_positives += 1
                    if len(examples) < 10:
                        examples.append((n, hlow, d, ys[-1] if ys else None))
            writer.writerow([
                "below-threshold", n, hlow, td, d, res.found,
                max(res.states_per_layer), f"{elapsed:.6f}"
            ])

    print(
        f"  below-threshold scan: {tested} searches; "
        f"{false_positives} residual false positives observed"
    )
    if examples:
        print("  first false-positive examples:")
        for ex in examples:
            print(f"    n={ex[0]}, h={ex[1]}, d={ex[2]}, exact endpoint={ex[3]}")


def preset_config(name: str):
    if name == "validation":
        return dict(
            order_N=11,
            theorem_A_s=4,
            theorem_A_m=35,
            theorem_B_h=3,
            min_graph_h=3,
            refinement_h=2,
            fiber_h4_samples=10,
            kappa_trials=2_000,
            path_trials=300,
            path_depth=12,
            path_q=1,
            target_max=35,
            target_radius=1,
            hard_limit=35,
            hard_top=2,
            hard_extra=1,
            hard_cap=20,
            below_max=35,
            below_radius=1,
            state_cap=2_000_000,
        )
    if name == "deep":
        return dict(
            order_N=14,
            theorem_A_s=5,
            theorem_A_m=101,
            theorem_B_h=4,
            min_graph_h=4,
            refinement_h=3,
            fiber_h4_samples=250,
            kappa_trials=50_000,
            path_trials=10_000,
            path_depth=40,
            path_q=2,
            target_max=199,
            target_radius=2,
            hard_limit=199,
            hard_top=12,
            hard_extra=3,
            hard_cap=55,
            below_max=99,
            below_radius=2,
            state_cap=5_000_000,
        )
    if name == "overnight":
        return dict(
            order_N=18,
            theorem_A_s=6,
            theorem_A_m=301,
            theorem_B_h=4,
            min_graph_h=4,
            refinement_h=3,
            fiber_h4_samples=1_000,
            kappa_trials=250_000,
            path_trials=50_000,
            path_depth=80,
            path_q=3,
            target_max=999,
            target_radius=3,
            hard_limit=999,
            hard_top=30,
            hard_extra=5,
            hard_cap=80,
            below_max=299,
            below_radius=3,
            state_cap=10_000_000,
        )
    raise ValueError(name)


def main() -> int:
    p = argparse.ArgumentParser(description="Deep computational falsification audit.")
    p.add_argument("--preset", choices=("validation", "deep", "overnight"), default="deep")
    args = p.parse_args()
    cfg = preset_config(args.preset)

    logs = HERE / "logs"
    results = HERE / "results"
    logs.mkdir(exist_ok=True)
    results.mkdir(exist_ok=True)
    csv_path = results / f"deep_audit_{args.preset}.csv"

    banner(f"DEEP COMPUTATIONAL AUDIT — preset={args.preset}")
    print("This is finite falsification work, not a mathematical proof.")
    print("Configuration:")
    for k, v in cfg.items():
        print(f"  {k} = {v}")

    t_all = time.perf_counter()

    with csv_path.open("w", newline="", encoding="utf-8-sig") as f:
        # Excel-friendly CSV for pt-BR/European locales: semicolon delimiter + UTF-8 BOM.
        writer = csv.writer(f, delimiter=";")
        writer.writerow([
            "test_type", "target_n", "h", "direct_depth", "tested_depth",
            "residual_nonempty", "max_states_in_layer", "elapsed_seconds"
        ])

        with timed("Higher-range exact structural checks"):
            c.test_order_64(cfg["order_N"])
            c.test_theorem_A(max_s=cfg["theorem_A_s"], max_m=cfg["theorem_A_m"])
            c.test_theorem_B(max_h=cfg["theorem_B_h"])
            c.test_min_graph(max_h=cfg["min_graph_h"])
            c.test_min_refinement(max_h_lower=cfg["refinement_h"])

        with timed("Sampled full fibers at h=4"):
            sampled_full_fibers(4, cfg["fiber_h4_samples"])

        with timed("Random kappa-isometry stress"):
            random_kappa_isometry(
                cfg["kappa_trials"], max_y=100_000, max_kappa=50_000
            )

        with timed("Deep exact-path realization / envelope stress"):
            deep_exact_path_stress(
                cfg["path_trials"], cfg["path_depth"], cfg["path_q"]
            )

        with timed("Broad target window sweep at h=h*(n)"):
            target_window_sweep(
                cfg["target_max"], cfg["target_radius"], cfg["state_cap"], writer
            )

        with timed("Every-depth sweep on the hardest targets"):
            all_depth_sweep_on_hard_targets(
                cfg["hard_limit"], cfg["hard_top"], cfg["hard_extra"],
                cfg["hard_cap"], cfg["state_cap"], writer
            )

        with timed("Below-threshold adversarial scan"):
            low_precision_adversarial_scan(
                cfg["below_max"], cfg["below_radius"], cfg["state_cap"], writer
            )

    elapsed = time.perf_counter() - t_all
    banner("DEEP AUDIT COMPLETE")
    print(f"No counterexample was found in the executed tests.")
    print(f"Excel-friendly CSV results: {csv_path}")
    print(f"If Microsoft Excel is installed, the Windows runner also converts this file to .xlsx automatically.")
    print(f"Total elapsed time: {elapsed:.3f} s")
    print("Again: this is finite computational evidence, not a proof.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
