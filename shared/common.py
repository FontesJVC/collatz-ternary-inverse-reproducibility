"""Shared arithmetic utilities for the Collatz companion papers."""
from __future__ import annotations

from fractions import Fraction
from typing import Tuple

D = (0, 1, 2)
INTERIOR_T = (1, 2)


def v3(n: int) -> int:
    if n == 0:
        raise ValueError("v3(0) undefined")
    n = abs(n)
    k = 0
    while n % 3 == 0:
        n //= 3
        k += 1
    return k


def rep_mod3pow(x: int, exp: int) -> int:
    return x % (3 ** exp)


def b_t_from_unit(y: int, t: int) -> int:
    """Return the unique base exponent b in {1,...,6} for inverse family t.

    It is enough that y be a unit modulo 3.  The exponent is characterized by
        2^b y == 1 + 3t (mod 9).
    """
    if t not in D:
        raise ValueError("t must be 0, 1, or 2")
    if y % 3 == 0:
        raise ValueError("y must be a unit modulo 3")
    target = (1 + 3 * t) % 9
    yy = y % 9
    for b in range(1, 7):
        if (pow(2, b, 9) * yy) % 9 == target:
            return b
    raise AssertionError("No base exponent found")


def odd_collatz_T(n: int) -> Tuple[int, int]:
    if n <= 0 or n % 2 == 0:
        raise ValueError("n must be positive odd")
    z = 3 * n + 1
    e = 0
    while z % 2 == 0:
        z //= 2
        e += 1
    return z, e


def reduced_depth_to_one(n: int, max_steps: int = 100000):
    if n <= 0 or n % 2 == 0:
        raise ValueError("n must be positive odd")
    seen = set()
    y = n
    path = [n]
    for d in range(max_steps + 1):
        if y == 1:
            return d, path
        if y in seen:
            return None
        seen.add(y)
        y, _ = odd_collatz_T(y)
        path.append(y)
    return None


def h_star(n: int) -> int:
    if n < 1 or n % 2 == 0:
        raise ValueError("n must be positive odd")
    rhs2 = 3 * (n + 1) ** 2
    h = 1
    while 2 * (3 ** (2 * h)) <= rhs2:
        h += 1
    return h


def envelope_U(n: int, remaining_depth: int) -> int:
    return int(Fraction(3, 2) ** remaining_depth * (n + 1) - 1)
