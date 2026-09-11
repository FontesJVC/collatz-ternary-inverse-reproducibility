#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
collatz_structural_audit.py

Computational laboratory for the residual/inverse Collatz structure discussed
in the preprint under development.

IMPORTANT
---------
This program DOES NOT prove the theorems. It:
  * checks identities on finite ranges;
  * searches for computational counterexamples;
  * reproduces examples (35, 85, 27);
  * tests the edge quotient, layered system, and Archimedean pruning;
  * compares the pruned residual search with the direct trajectory only as a control.

Python standard library only.

Examples:
    python collatz_structural_audit.py
    python collatz_structural_audit.py --suite full
    python collatz_structural_audit.py --target 35 --max-depth 6
    python collatz_structural_audit.py --target 27 --max-depth 45 --no-search
    python collatz_structural_audit.py --target 35 --h 1 --max-depth 4
"""

from __future__ import annotations

import argparse
import math
import random
import sys

# Force UTF-8 output when possible.  This avoids Windows cp1252/charmap
# failures on mathematical Unicode labels when stdout is redirected to a log.
for _stream in (sys.stdout, sys.stderr):
    try:
        _stream.reconfigure(encoding="utf-8", errors="replace")
    except (AttributeError, ValueError):
        pass
from collections import Counter, deque
from dataclasses import dataclass
from fractions import Fraction
from typing import Dict, Iterable, List, Optional, Sequence, Tuple

D = (0, 1, 2)
INTERIOR_T = (1, 2)


# ---------------------------------------------------------------------------
# Arithmetic utilities
# ---------------------------------------------------------------------------

def v3(n: int) -> int:
    """3-adic valuation of n != 0."""
    if n == 0:
        raise ValueError("v3(0) is not used in this script.")
    n = abs(n)
    k = 0
    while n % 3 == 0:
        n //= 3
        k += 1
    return k


def odd_collatz_T(n: int) -> Tuple[int, int]:
    """
    Accelerated odd dynamics:
        T(n) = (3n+1)/2^e
    Returns (T(n), e).
    """
    if n <= 0 or n % 2 == 0:
        raise ValueError("n must be a positive odd integer.")
    z = 3 * n + 1
    e = 0
    while z % 2 == 0:
        z //= 2
        e += 1
    return z, e


def rep_mod(x: int, exponent: int) -> int:
    """Least representative in [0,3^exponent-1]."""
    return x % (3 ** exponent)


def modinv(a: int, m: int) -> int:
    return pow(a, -1, m)


def floor_log2_fraction(x: Fraction) -> int:
    """Largest integer K such that 2^K <= x, for x >= 1, without floating point."""
    if x < 1:
        raise ValueError("x must be >= 1")
    num, den = x.numerator, x.denominator
    # initial guess from bit_length
    k = max(0, num.bit_length() - den.bit_length() - 1)
    while (1 << (k + 1)) * den <= num:
        k += 1
    while (1 << k) * den > num:
        k -= 1
    return k


def h_star(n: int) -> int:
    """
    Smallest h>=1 such that:
        3^(2h) > (3/2)(n+1)^2
    using exact integer arithmetic.
    """
    if n < 1:
        raise ValueError("n must be >= 1")
    h = 1
    rhs2 = 3 * (n + 1) ** 2  # compare 2*3^(2h) > rhs2
    while 2 * (3 ** (2 * h)) <= rhs2:
        h += 1
    return h


# ---------------------------------------------------------------------------
# Exact families (t,q)
# ---------------------------------------------------------------------------

def b_t_from_unit(y: int, t: int) -> int:
    """
    Unique b in {1,...,6} such that 2^b y == 1+3t (mod 9).
    It is enough that y be a unit modulo 3.
    """
    if t not in D:
        raise ValueError("t must be 0,1,2")
    if y % 3 == 0:
        raise ValueError("y must be a unit modulo 3")
    target = (1 + 3 * t) % 9
    yy = y % 9
    for b in range(1, 7):
        if (pow(2, b, 9) * yy) % 9 == target:
            return b
    raise AssertionError("Could not find b_t; this should not happen.")


def inverse_child(y: int, t: int, q: int) -> Tuple[int, int]:
    """
    Exact inverse child:
        x = (2^(b_t(y)+6q)y - 1)/3
    Returns (x, total_exponent).
    """
    if y <= 0 or y % 2 == 0 or y % 3 == 0:
        raise ValueError("y must lie in the interior I: positive, odd, and not divisible by 3.")
    if q < 0:
        raise ValueError("q must be >= 0")
    b = b_t_from_unit(y, t)
    e = b + 6 * q
    num = (1 << e) * y - 1
    assert num % 3 == 0
    x = num // 3
    assert x % 2 == 1
    assert x % 3 == t
    return x, e


def q_from_exact_edge(y: int, x: int) -> Tuple[int, int, int]:
    """
    Given an exact integer edge y -> x, recover (t,q,e).
    Fails if the pair is not an edge of the accelerated odd dynamics.
    """
    if y <= 0 or x <= 0 or y % 2 == 0 or x % 2 == 0 or y % 3 == 0:
        raise ValueError("Invalid domain.")
    if 3 * x + 1 <= 0:
        raise ValueError
    ratio_num = 3 * x + 1
    if ratio_num % y != 0:
        raise ValueError("Not an exact edge.")
    p = ratio_num // y
    if p <= 0 or p & (p - 1):
        raise ValueError("Ratio is not a power of 2.")
    e = p.bit_length() - 1
    t = x % 3
    b = b_t_from_unit(y, t)
    if e < b or (e - b) % 6 != 0:
        raise ValueError("Exponent does not belong to the expected family.")
    q = (e - b) // 6
    return t, q, e


# ---------------------------------------------------------------------------
# Local edge quotient
# ---------------------------------------------------------------------------

def phi_full(h: int, r: int, k: int, t: int, q: int) -> int:
    """
    Phi_h^full(r;k,t,q) modulo M_h=3^(2h).
    r is a unit residue class represented by an int.
    """
    if h < 1:
        raise ValueError("h>=1")
    if k not in D or t not in D or q < 0:
        raise ValueError
    M = 3 ** (2 * h)
    rho = r % M
    if rho % 3 == 0:
        raise ValueError("r must be a unit.")
    Y = rho + k * M
    b = b_t_from_unit(rho, t)
    num = pow(2, b + 6 * q) * Y - 1
    assert num % 3 == 0
    return (num // 3) % M


def units_mod_3pow(exp: int) -> List[int]:
    m = 3 ** exp
    return [r for r in range(m) if r % 3 != 0]


def test_order_64(max_N: int = 9) -> None:
    print("\n[TEST] order of 64 modulo 3^N")
    for N in range(2, max_N + 1):
        mod = 3 ** N
        expected = 3 ** (N - 2)
        if pow(64, expected, mod) != 1:
            raise AssertionError(f"64^{expected} != 1 mod 3^{N}")
        # For a power of 3, it is enough to check that exponent/3 does not work, when applicable.
        if expected > 1 and pow(64, expected // 3, mod) == 1:
            raise AssertionError(f"order smaller than expected at N={N}")
    print(f"  OK for N=2,...,{max_N}")


def test_theorem_C(max_h: int = 2, sample_h3: int = 100) -> None:
    """
    Tests the bijection qbar -> X_{h,t}.
    Exhaustive through max_h; if max_h<3, sample at h=3.
    """
    print("\n[TEST] Theorem C: q-bar parametrizes the fiber X_{h,t} exactly")
    rng = random.Random(12345)

    for h in range(1, max_h + 1):
        M = 3 ** (2 * h)
        Q = 3 ** (2 * h - 1)
        units = units_mod_3pow(2 * h)
        expected_fibers = {
            t: {x for x in range(M) if x % 3 == t}
            for t in D
        }
        checked = 0
        for r in units:
            for k in D:
                for t in D:
                    vals = {phi_full(h, r, k, t, q) for q in range(Q)}
                    if vals != expected_fibers[t]:
                        raise AssertionError(
                            f"Theorem C failure: h={h},r={r},k={k},t={t}"
                        )
                    checked += 1
        print(f"  h={h}: OK ({checked} fibers checked exhaustively)")

    if max_h < 3 and sample_h3:
        h = 3
        M = 3 ** 6
        Q = 3 ** 5
        units = units_mod_3pow(6)
        for _ in range(sample_h3):
            r = rng.choice(units)
            k = rng.choice(D)
            t = rng.choice(D)
            vals = {phi_full(h, r, k, t, q) for q in range(Q)}
            expected = {x for x in range(M) if x % 3 == t}
            if vals != expected:
                raise AssertionError(f"Sample failure at h=3,r={r},k={k},t={t}")
        print(f"  h=3: OK on {sample_h3} random fibers")


# ---------------------------------------------------------------------------
# Theorem A / signatures / states
# ---------------------------------------------------------------------------

def F(m: int) -> int:
    return (pow(4, m) - 1) // 3


def tau_hat(s: int, y: int) -> int:
    """Canonical representative tau_s."""
    if s < 0 or y % 3 == 0:
        raise ValueError
    mod = 3 ** (s + 1)
    period = 2 * (3 ** s)
    yy = y % mod
    for e in range(period):
        if (pow(2, e, mod) * yy) % mod == 1:
            return e
    raise AssertionError("tau_hat not found.")


def H_hat(s: int, m: int) -> int:
    return tau_hat(s, F(m))


def R_residual(s: int, h: int, m: int, u: int) -> int:
    if not (s >= h >= 1):
        raise ValueError("Requires s>=h>=1")
    num = H_hat(s + h - 1, m + (3 ** s) * u) - H_hat(s - 1, m)
    den = 2 * (3 ** (s - 1))
    if num % den != 0:
        raise AssertionError("Residual block is not an integer.")
    return (num // den) % (3 ** h)


def alpha_beta_residual(s: int, h: int, m: int) -> Tuple[int, int]:
    if not (s >= h >= 1 and m >= 1 and m % 3 != 0):
        raise ValueError
    modh = 3 ** h
    vs_num = pow(4, 3 ** (s - 1)) - 1
    vs_den = 3 ** s
    assert vs_num % vs_den == 0
    vs = vs_num // vs_den
    e0 = H_hat(s - 1, m)
    fm = F(m)
    ks_num = pow(2, e0) * fm - 1
    assert ks_num % (3 ** s) == 0
    Ks = ks_num // (3 ** s)
    alpha = (-modinv(vs % modh, modh) * Ks) % modh
    beta = (-pow(4, m, modh) * modinv(fm % modh, modh)) % modh
    return alpha, beta


def test_theorem_A(max_s: int = 4, max_m: int = 25) -> None:
    print("\n[TEST] Theorem A: residual affinity")
    cases = 0
    for s in range(1, max_s + 1):
        for h in range(1, s + 1):
            modh = 3 ** h
            for m in range(1, max_m + 1):
                if m % 3 == 0:
                    continue
                a, b = alpha_beta_residual(s, h, m)
                for u in range(3 ** h):
                    lhs = R_residual(s, h, m, u)
                    rhs = (a + b * u) % modh
                    if lhs != rhs:
                        raise AssertionError(
                            f"Theorem A failure: s={s},h={h},m={m},u={u}, {lhs}!={rhs}"
                        )
                if math.gcd(b, 3) != 1:
                    raise AssertionError("beta should be a unit.")
                cases += 1
    print(f"  OK on {cases} (s,h,m) blocks, with every u in each block")


def state_S(h: int, y: int) -> Tuple[int, int]:
    if y % 3 == 0:
        raise ValueError
    modh = 3 ** h
    alpha_num = tau_hat(2 * h - 1, y) - tau_hat(h - 1, y)
    alpha_den = 2 * (3 ** (h - 1))
    assert alpha_num % alpha_den == 0
    alpha = (alpha_num // alpha_den) % modh
    beta = (-(3 * y + 1) * modinv(y % modh, modh)) % modh
    return alpha, beta


def test_theorem_B(max_h: int = 3) -> None:
    print("\n[TEST] Theorem B: state classification")
    for h in range(1, max_h + 1):
        M = 3 ** (2 * h)
        states: Dict[Tuple[int, int], int] = {}
        for r in range(M):
            if r % 3 == 0:
                continue
            s = state_S(h, r)
            if s in states and states[s] != r:
                raise AssertionError(f"Collision at h={h}: {states[s]}, {r} -> {s}")
            states[s] = r
        expected = 2 * (3 ** (2 * h - 1))
        if len(states) != expected:
            raise AssertionError(f"Incorrect N_h at h={h}")
        print(f"  h={h}: OK, {len(states)} distinct states")


# ---------------------------------------------------------------------------
# q=0: degree, connectivity, refinement
# ---------------------------------------------------------------------------

def min_graph_adjacency(h: int) -> Dict[int, List[int]]:
    M = 3 ** (2 * h)
    adj: Dict[int, List[int]] = {}
    for r in units_mod_3pow(2 * h):
        dests = []
        for k in D:
            for t in INTERIOR_T:
                dests.append(phi_full(h, r, k, t, 0))
        adj[r] = dests
    return adj


def reachable(adj: Dict[int, List[int]], start: int) -> set:
    seen = {start}
    dq = deque([start])
    while dq:
        u = dq.popleft()
        for v in adj.get(u, []):
            if v not in seen:
                seen.add(v)
                dq.append(v)
    return seen


def test_min_graph(max_h: int = 3) -> None:
    print("\n[TEST] q=0 subsystem: degree 6 and strong connectivity")
    for h in range(1, max_h + 1):
        adj = min_graph_adjacency(h)
        verts = set(adj)
        indeg = Counter()
        for r, ds in adj.items():
            if len(ds) != 6 or len(set(ds)) != 6:
                raise AssertionError(f"Out-degree/distinctness failed at h={h}, r={r}")
            for x in ds:
                if x not in verts:
                    raise AssertionError("Destination should be interior.")
                indeg[x] += 1
        if any(indeg[v] != 6 for v in verts):
            bad = [(v, indeg[v]) for v in verts if indeg[v] != 6][:5]
            raise AssertionError(f"Indegree !=6 em h={h}: {bad}")

        # Conectividade forte: alcance em G e G^T desde 1.
        if reachable(adj, 1) != verts:
            raise AssertionError(f"1 does not reach every vertex at h={h}")
        rev = {v: [] for v in verts}
        for u, ds in adj.items():
            for v in ds:
                rev[v].append(u)
        if reachable(rev, 1) != verts:
            raise AssertionError(f"Not every vertex reaches 1 at h={h}")
        print(f"  h={h}: OK ({len(verts)} vertices, degree 6, strongly connected)")


def test_min_refinement(max_h_lower: int = 2) -> None:
    print("\n[TEST] 9-to-1 refinement of the q=0 subsystem")
    checked = 0
    for h in range(1, max_h_lower + 1):
        M = 3 ** (2 * h)
        M2 = 9 * M
        for r in units_mod_3pow(2 * h):
            rho = r % M
            for k in D:
                for t in D:
                    low = phi_full(h, r, k, t, 0)
                    targets = []
                    for c in D:
                        R = (rho + M * (k + 3 * c)) % M2
                        for K in D:
                            up = phi_full(h + 1, R, K, t, 0)
                            if up % M != low:
                                raise AssertionError(
                                    f"Projection failed at h={h},r={r},k={k},t={t},c={c},K={K}"
                                )
                            targets.append(up)
                    expected = {(low + a * M) % M2 for a in range(9)}
                    if set(targets) != expected or len(set(targets)) != 9:
                        raise AssertionError(
                            f"Ninefold lifting failed at h={h},r={r},k={k},t={t}"
                        )
                    checked += 1
        print(f"  h={h}->h={h+1}: OK")
    print(f"  {checked} lower edges checked")


# ---------------------------------------------------------------------------
# Exact paths, C_h(w), q precision
# ---------------------------------------------------------------------------

@dataclass
class ExactStep:
    y: int
    t: int
    q: int
    b: int
    y_next: int


def build_exact_inverse_path(y0: int, labels: Sequence[Tuple[int, int]]) -> List[ExactStep]:
    y = y0
    out = []
    for t, q in labels:
        x, e = inverse_child(y, t, q)
        out.append(ExactStep(y=y, t=t, q=q, b=e, y_next=x))
        y = x
    return out


def fixed_h_path_data(h: int, steps: Sequence[ExactStep]):
    M = 3 ** (2 * h)
    data = []
    for st in steps:
        r = st.y % M
        rho = r
        k = ((st.y - rho) // M) % 3
        r_next = st.y_next % M
        b0 = b_t_from_unit(rho, st.t)
        assert st.b == b0 + 6 * st.q
        if phi_full(h, r, k, st.t, st.q) != r_next:
            raise AssertionError("Exact-path projection failed.")
        data.append((r, k, st.t, st.q, st.b, r_next))
    return data


def AB_from_exponents(exps: Sequence[int]) -> Tuple[int, int]:
    A = 0
    B = 0
    for j, e in enumerate(exps):
        A += e
        B = (1 << e) * B + (3 ** j)
    return A, B


def C_h_from_path(h: int, terminal_r: int, exps: Sequence[int]) -> int:
    d = len(exps)
    A, B = AB_from_exponents(exps)
    mod = 3 ** (2 * h + d)
    return (pow(2, -A, mod) * (B + (3 ** d) * (terminal_r % (3 ** (2 * h))))) % mod


def test_path_realization_random(trials: int = 300) -> None:
    print("\n[TEST] finite realization / C_h(w) class on random exact trajectories")
    rng = random.Random(20260910)
    for _ in range(trials):
        h = rng.randint(1, 3)
        d = rng.randint(1, 5)
        # positive odd interior source
        while True:
            y0 = rng.randrange(1, 400, 2)
            if y0 % 3:
                break
        labels = [(rng.choice(INTERIOR_T), rng.randint(0, 2)) for _ in range(d)]
        steps = build_exact_inverse_path(y0, labels)
        fixed_h_path_data(h, steps)
        terminal = steps[-1].y_next
        exps = [s.b for s in steps]
        C = C_h_from_path(h, terminal % (3 ** (2 * h)), exps)
        mod = 3 ** (2 * h + d)
        if y0 % mod != C:
            raise AssertionError(
                f"C_h falhou: h={h},d={d},y0={y0},C={C},mod={mod}"
            )
    print(f"  OK on {trials} random trajectories")


def test_q_precision_random(trials: int = 500) -> None:
    print("\n[TEST] q_j precision modulo 3^(N-2) in one transition")
    rng = random.Random(314159)
    for _ in range(trials):
        N = rng.randint(3, 9)
        mod_src = 3 ** N
        mod_dst = 3 ** (N - 1)
        while True:
            Y = rng.randrange(1, mod_src)
            if Y % 3:
                break
        t = rng.choice(D)
        b = b_t_from_unit(Y, t)
        q = rng.randint(0, 100)
        delta = (3 ** (N - 2)) * rng.randint(0, 5)
        q2 = q + delta
        z1 = (((1 << b) * pow(64, q) * Y - 1) // 3) % mod_dst
        z2 = (((1 << b) * pow(64, q2) * Y - 1) // 3) % mod_dst
        if z1 != z2:
            raise AssertionError(f"q precision failed at N={N}")
    print(f"  OK on {trials} random cases")


def test_k_recovery_random(trials: int = 500) -> None:
    print("\n[TEST] recovery of k from the refined vertex")
    rng = random.Random(271828)
    for _ in range(trials):
        h = rng.randint(1, 3)
        d = rng.randint(1, 6)
        j = rng.randint(0, d - 1)
        N = 2 * h + d - j
        mod = 3 ** N
        M = 3 ** (2 * h)
        while True:
            R = rng.randrange(mod)
            if R % 3:
                break
        r = R % M
        k1 = ((R - r) // M) % 3
        k2 = (R // M) % 3  # r is the canonical remainder <M
        if k1 != k2:
            raise AssertionError("Recovery of k failed.")
    print(f"  OK on {trials} random cases")


# ---------------------------------------------------------------------------
# Archimedean envelope and target-pruned system
# ---------------------------------------------------------------------------

def U(n: int, d: int, j: int) -> Fraction:
    if not (0 <= j <= d):
        raise ValueError
    return (Fraction(3, 2) ** (d - j)) * (n + 1) - 1


def L_bound(n: int, d: int, j: int) -> Fraction:
    if not (0 <= j < d):
        raise ValueError
    return 3 * U(n, d, j + 1) + 1


def qmax_specific(n: int, d: int, j: int, b: int) -> int:
    """Largest q>=0 allowed by the specific bound; -1 if the family is impossible."""
    K = floor_log2_fraction(L_bound(n, d, j))
    return (K - b) // 6


def min_positive_odd_in_class(R: int, N: int, interior: bool = True) -> Optional[int]:
    """
    Smallest positive odd integer in the class R mod 3^N.
    Returns None if interior=True and the class is 0 mod 3.
    """
    m = 3 ** N
    r = R % m
    if interior and r % 3 == 0:
        return None
    if r > 0 and r % 2 == 1:
        return r
    # m is odd, so adding m flips parity.
    y = r + m
    if y <= 0 or y % 2 == 0:
        raise AssertionError("Failed to construct an odd representative.")
    if interior and y % 3 == 0:
        return None
    return y


def vertex_survives(R: int, N: int, bound: Fraction, interior: bool = True) -> bool:
    y = min_positive_odd_in_class(R, N, interior=interior)
    return y is not None and Fraction(y, 1) <= bound


@dataclass
class LayerEdge:
    layer: int
    R: int
    t: int
    q: int
    b_total: int
    R_next: int


@dataclass
class SearchResult:
    found: bool
    path: List[LayerEdge]
    states_per_layer: List[int]
    h: int
    d: int
    n: int


def layered_pruned_search(n: int, d: int, h: int, reduced_root_loop: bool = True,
                          state_cap: int = 2_000_000) -> SearchResult:
    """
    Target-pruned residual search P_{h,d}(n), using exact q values only within the
    admissible Archimedean interval. Since qmax is finite, this is a finite search.

    For h at or above h_star(n), the theorem predicts equivalence with the exact trajectory
    exact integer trajectory of depth d.

    Returns a witness path if one exists.
    """
    if n < 1 or n % 2 == 0:
        raise ValueError("This script handles positive odd targets.")
    if d < 1 or h < 1:
        raise ValueError

    N0 = 2 * h + d
    start_mod = 3 ** N0
    start_R = 1 % start_mod

    # residue -> (prev_residue, edge)
    current = {start_R: None}
    predecessors: List[Dict[int, Tuple[int, LayerEdge]]] = []
    counts = [1]

    for j in range(d):
        N = 2 * h + d - j
        Nnext = N - 1
        m = 3 ** N
        mnext = 3 ** Nnext
        next_map: Dict[int, Tuple[int, LayerEdge]] = {}

        last = (j == d - 1)
        allowed_t = list(INTERIOR_T)
        if last and n % 3 == 0:
            allowed_t.append(0)

        for R in current:
            # For a surviving vertex, use the canonical representative of the class
            # to define the residual transition. At low precision this can produce
            # wrap-around; this is precisely the relaxation we want to observe.
            yrep = R % m
            if yrep % 3 == 0:
                continue

            for t in allowed_t:
                b0 = b_t_from_unit(yrep, t)
                qmax = qmax_specific(n, d, j, b0)
                if qmax < 0:
                    continue

                for q in range(qmax + 1):
                    e = b0 + 6 * q
                    num = (1 << e) * yrep - 1
                    if num % 3 != 0:
                        raise AssertionError("The base exponent should guarantee divisibility.")
                    z = num // 3
                    R2 = z % mnext

                    # reduced tree: remove only the trivial integer loop 1->1.
                    if reduced_root_loop and yrep == 1 and t == 1 and q == 0 and z == 1:
                        continue

                    interior_dest = not (last and t == 0)
                    if not vertex_survives(R2, Nnext, U(n, d, j + 1), interior=interior_dest):
                        continue

                    # No terminal fixamos exatamente a CLASSE de n.
                    if last and R2 != n % mnext:
                        continue

                    edge = LayerEdge(
                        layer=j, R=R, t=t, q=q, b_total=e, R_next=R2
                    )
                    if R2 not in next_map:
                        next_map[R2] = (R, edge)

        predecessors.append(next_map)
        current = {R: None for R in next_map}
        counts.append(len(current))

        if len(current) > state_cap:
            raise RuntimeError(
                f"Busca excedeu state_cap={state_cap} na camada {j+1}; "
                f"use --no-search, menor d ou aumente --state-cap."
            )

        if not current:
            return SearchResult(False, [], counts, h, d, n)

    target_R = n % (3 ** (2 * h))
    if target_R not in current:
        return SearchResult(False, [], counts, h, d, n)

    # Reconstruct witness.
    path_rev: List[LayerEdge] = []
    Rcur = target_R
    for j in range(d - 1, -1, -1):
        prev_R, edge = predecessors[j][Rcur]
        path_rev.append(edge)
        Rcur = prev_R
    path_rev.reverse()
    return SearchResult(True, path_rev, counts, h, d, n)


def exact_integers_from_layer_path(result: SearchResult) -> List[int]:
    """
    Replays the integer trajectory using the q values stored on the path, starting at 1.
    Useful as a post-search control. At low precision it may diverge from the representatives.
    """
    if not result.found:
        return []
    ys = [1]
    y = 1
    for edge in result.path:
        b0 = b_t_from_unit(y, edge.t)
        e = b0 + 6 * edge.q
        num = (1 << e) * y - 1
        if num % 3:
            return ys + [None]  # should not occur
        y = num // 3
        ys.append(y)
    return ys


def direct_reduced_depth(n: int, max_steps: int = 10000) -> Optional[Tuple[int, List[int], List[int]]]:
    """
    External control: computes the DIRECT odd trajectory of n until its first arrival at 1.
    Returns (depth, nodes, exponents), or None if 1 is not reached within the limit.
    It is not used to decide the residual search.
    """
    if n < 1 or n % 2 == 0:
        raise ValueError
    if n == 1:
        return 0, [1], []
    y = n
    nodes = [n]
    exps = []
    seen = {n}
    for step in range(1, max_steps + 1):
        y, e = odd_collatz_T(y)
        exps.append(e)
        nodes.append(y)
        if y == 1:
            return step, nodes, exps
        if y in seen:
            return None
        seen.add(y)
    return None


def print_search_result(result: SearchResult, show_exact_control: bool = True) -> None:
    status = "NONEMPTY" if result.found else "empty"
    print(
        f"  n={result.n}, h={result.h}, d={result.d}: {status}; "
        f"states per layer={result.states_per_layer}"
    )
    if result.found:
        labels = [(e.t, e.q) for e in result.path]
        print(f"    witness labels (t,q): {labels}")
        if show_exact_control:
            ys = exact_integers_from_layer_path(result)
            print(f"    integer trajectory generated by the labels: {ys}")
            if ys and ys[-1] == result.n:
                print("    -> witness is EXACT for the target.")
            else:
                print("    -> residual witness does NOT end exactly at the target (false positive).")


def test_envelope_on_random_exact_paths(trials: int = 300) -> None:
    print("\n[TEST] Archimedean envelope on random exact paths")
    rng = random.Random(424242)
    for _ in range(trials):
        d = rng.randint(1, 6)
        while True:
            y0 = rng.randrange(1, 100, 2)
            if y0 % 3:
                break
        labels = [(rng.choice(INTERIOR_T), rng.randint(0, 1)) for _ in range(d)]
        steps = build_exact_inverse_path(y0, labels)
        ys = [y0] + [s.y_next for s in steps]
        n = ys[-1]
        for j, y in enumerate(ys):
            if Fraction(y, 1) > U(n, d, j):
                raise AssertionError(
                    f"Envelope failed: y0={y0},n={n},d={d},j={j},y={y},U={U(n,d,j)}"
                )
        for j, st in enumerate(steps):
            if (1 << st.b) > L_bound(n, d, j):
                raise AssertionError("Exponent bound failed.")
    print(f"  OK on {trials} random trajectories")


def test_finite_precision_exactness(targets: Sequence[int] = (5, 7, 11, 13, 17, 23, 35, 53, 85),
                                    max_d: int = 7) -> None:
    """
    Compares nonemptiness of the pruned search at h_star(n) with the direct depth
    for small targets. This is a computational test, not a proof.
    """
    print("\n[TEST] finite-precision exactness: pruned search vs direct control")
    for n in targets:
        if n % 2 == 0:
            continue
        hs = h_star(n)
        direct = direct_reduced_depth(n, max_steps=1000)
        true_d = None if direct is None else direct[0]
        tested = []
        for d in range(1, max_d + 1):
            res = layered_pruned_search(n, d, hs)
            tested.append((d, res.found))
            should = (true_d == d)
            if res.found != should:
                raise AssertionError(
                    f"Mismatch n={n},h*={hs},d={d}: residual={res.found}, direct={should}"
                )
        print(f"  n={n:>3}, h*={hs}, direct depth={true_d}, tests={tested}")
    print("  OK on the tested targets")


# ---------------------------------------------------------------------------
# Examples 35, 85, 27
# ---------------------------------------------------------------------------

def demo_35(max_depth: int = 6, h: Optional[int] = None) -> None:
    print("\n[DEMO] target 35")
    hs = h_star(35) if h is None else h
    print(f"  h used = {hs}; h*(35) = {h_star(35)}")
    print(f"  M=3^(2h)={3**(2*hs)}")
    print(f"  threshold (3/2)(36)^2 = {Fraction(3,2)*36**2}")
    for d in range(1, max_depth + 1):
        res = layered_pruned_search(35, d, hs)
        print_search_result(res, show_exact_control=True)


def demo_85() -> None:
    print("\n[DEMO] 1 -> 85")
    x0, e0 = inverse_child(1, 1, 0)
    x1, e1 = inverse_child(1, 1, 1)
    print(f"  (t,q)=(1,0): 1 -> {x0}, exponent {e0}")
    print(f"  (t,q)=(1,1): 1 -> {x1}, exponent {e1}")
    assert x1 == 85 and e1 == 8
    for h in (1, 2, 3):
        M = 3 ** (2 * h)
        rdest = phi_full(h, 1, 0, 1, 1)
        print(f"  h={h}: [1] -> [{rdest}] mod {M}; 85 mod M = {85 % M}")


def demo_27() -> None:
    print("\n[DEMO] direct odd trajectory of 27 (control/example only)")
    data = direct_reduced_depth(27, max_steps=1000)
    if data is None:
        print("  Did not reach 1 within the limit.")
        return
    depth, nodes, exps = data
    print(f"  reduced depth = {depth}")
    print(f"  number of exponents = {len(exps)}")
    print(f"  largest observed exponent = {max(exps)}")
    print(f"  h*(27) = {h_star(27)}")
    print(f"  first direct nodes: {nodes[:10]}")
    print(f"  last direct nodes:    {nodes[-10:]}")
    # Reconstruct inverse address and q values
    inv_nodes = list(reversed(nodes))
    labels = []
    qs = []
    for y, x in zip(inv_nodes[:-1], inv_nodes[1:]):
        t, q, e = q_from_exact_edge(y, x)
        labels.append((t, q, e))
        qs.append(q)
    print(f"  are all q values in the inverse address zero? {all(q == 0 for q in qs)}")
    print(f"  largest observed q = {max(qs) if qs else 0}")


# ---------------------------------------------------------------------------
# Additional low-precision / false-positive tests
# ---------------------------------------------------------------------------

def demo_low_precision_false_positive() -> None:
    print("\n[DEMO] low precision may leave a false positive: n=35,d=4,h=1")
    res = layered_pruned_search(35, 4, 1)
    print_search_result(res, show_exact_control=True)
    print("  Compare with h*=4:")
    res2 = layered_pruned_search(35, 4, h_star(35))
    print_search_result(res2, show_exact_control=True)


# ---------------------------------------------------------------------------
# Runner
# ---------------------------------------------------------------------------

def run_quick_suite() -> None:
    test_order_64(8)
    test_theorem_A(max_s=3, max_m=14)
    test_theorem_B(max_h=2)
    test_theorem_C(max_h=2, sample_h3=30)
    test_min_graph(max_h=3)
    test_min_refinement(max_h_lower=1)
    test_q_precision_random(200)
    test_k_recovery_random(200)
    test_path_realization_random(120)
    test_envelope_on_random_exact_paths(120)
    test_finite_precision_exactness(
        targets=(5, 7, 11, 13, 17, 23, 35, 53, 85),
        max_d=6,
    )
    demo_85()
    demo_35(max_depth=5)
    demo_low_precision_false_positive()
    demo_27()


def run_full_suite() -> None:
    test_order_64(10)
    test_theorem_A(max_s=4, max_m=35)
    test_theorem_B(max_h=3)
    test_theorem_C(max_h=3, sample_h3=0)
    test_min_graph(max_h=3)
    test_min_refinement(max_h_lower=2)
    test_q_precision_random(2000)
    test_k_recovery_random(2000)
    test_path_realization_random(1500)
    test_envelope_on_random_exact_paths(1500)
    test_finite_precision_exactness(
        targets=tuple(n for n in range(1, 100, 2)),
        max_d=10,
    )
    demo_85()
    demo_35(max_depth=7)
    demo_low_precision_false_positive()
    demo_27()


def parse_args(argv: Optional[Sequence[str]] = None) -> argparse.Namespace:
    p = argparse.ArgumentParser(
        description="Computational audit of the residual/inverse Collatz structure."
    )
    p.add_argument(
        "--suite", choices=("quick", "full", "none"), default="quick",
        help="Automatic test suite (default: quick)."
    )
    p.add_argument("--target", type=int, help="Odd target for target-pruned search.")
    p.add_argument("--h", type=int, help="Horizon h. Default for a target: h*(n).")
    p.add_argument(
        "--max-depth", type=int, default=6,
        help="Maximum search depth for --target (default: 6)."
    )
    p.add_argument(
        "--no-search", action="store_true",
        help="Do not run residual search for --target; show only direct control/h*."
    )
    p.add_argument(
        "--state-cap", type=int, default=2_000_000,
        help="Maximum number of states per layer in the search (default: 2,000,000)."
    )
    return p.parse_args(argv)


def main(argv: Optional[Sequence[str]] = None) -> int:
    args = parse_args(argv)

    print("=" * 78)
    print("COMPUTATIONAL AUDIT — RESIDUAL/INVERSE COLLATZ STRUCTURE")
    print("=" * 78)
    print("Warning: computational results do not replace mathematical proofs.")

    try:
        if args.suite == "quick":
            run_quick_suite()
        elif args.suite == "full":
            run_full_suite()

        if args.target is not None:
            n = args.target
            if n < 1 or n % 2 == 0:
                raise ValueError("--target must be a positive odd integer.")
            hs = h_star(n) if args.h is None else args.h
            print("\n" + "=" * 78)
            print(f"CUSTOM TARGET n={n}")
            print("=" * 78)
            print(f"h*(n) = {h_star(n)}; h used = {hs}")
            print(
                f"3^(2h)={3**(2*hs)}; "
                f"(3/2)(n+1)^2={Fraction(3,2)*(n+1)**2}"
            )

            direct = direct_reduced_depth(n, max_steps=100000)
            if direct is None:
                print("Direct control: did not reach 1 within the limit / a repetition was detected.")
            else:
                print(f"Direct control: reduced depth = {direct[0]}")

            if not args.no_search:
                for d in range(1, args.max_depth + 1):
                    res = layered_pruned_search(
                        n, d, hs,
                        reduced_root_loop=True,
                        state_cap=args.state_cap
                    )
                    print_search_result(res, show_exact_control=True)

    except AssertionError as exc:
        print("\n*** COUNTEREXAMPLE / TEST FAILURE FOUND ***")
        print(exc)
        return 2
    except Exception as exc:
        print("\n*** EXECUTION ERROR ***")
        print(type(exc).__name__ + ":", exc)
        return 1

    print("\n" + "=" * 78)
    print("END — no counterexample was found in the executed tests.")
    print("This is finite computational evidence, not a proof.")
    print("=" * 78)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
