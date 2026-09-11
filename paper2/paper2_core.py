"""Full edge-code and layered-system helpers (Paper 2)."""
from __future__ import annotations

from dataclasses import dataclass
from typing import List, Optional, Tuple
from shared.common import D, b_t_from_unit, h_star, envelope_U


def inverse_child(y: int, t: int, q: int) -> Tuple[int, int]:
    if y <= 0 or y % 2 == 0 or y % 3 == 0:
        raise ValueError("y must be a positive odd unit")
    if q < 0:
        raise ValueError("q must be nonnegative")
    b = b_t_from_unit(y, t)
    e = b + 6 * q
    num = (1 << e) * y - 1
    assert num % 3 == 0
    x = num // 3
    assert x % 2 == 1
    return x, e


def kappa_of(t: int, q: int) -> int:
    return t + 3 * q


def t_q_of_kappa(kappa: int) -> Tuple[int, int]:
    if kappa < 0:
        raise ValueError("kappa must be nonnegative")
    t = kappa % 3
    q = (kappa - t) // 3
    return t, q


def xi_y(y: int, kappa: int) -> int:
    t, q = t_q_of_kappa(kappa)
    x, _ = inverse_child(y, t, q)
    return x


def finite_xi_mod(y: int, R: int) -> List[int]:
    mod = 3 ** R
    return [xi_y(y, k) % mod for k in range(mod)]


def valuation_isometry_holds(y: int, Kmax: int) -> bool:
    from shared.common import v3
    for a in range(Kmax + 1):
        for b in range(Kmax + 1):
            if a == b:
                continue
            lhs = v3(xi_y(y, a) - xi_y(y, b))
            rhs = v3(a - b)
            if lhs != rhs:
                return False
    return True


def layered_moduli(h: int, d: int) -> List[int]:
    return [2 * h + d - j for j in range(d + 1)]


def no_wrap_bound_holds(n: int, h: int) -> bool:
    """Test 3^(2h) > (3/2)(n+1)^2 using exact integer arithmetic."""
    return 2 * 3 ** (2 * h) > 3 * (n + 1) ** 2


def smallest_uniform_terminal_horizon(n: int) -> int:
    return h_star(n)


def forward_exact_path_from_one(target: int, max_steps: int = 100000) -> Optional[List[int]]:
    """Return reversed reduced odd path 1 -> ... -> target if target reaches 1."""
    from shared.common import reduced_depth_to_one, odd_collatz_T
    out = reduced_depth_to_one(target, max_steps=max_steps)
    if out is None:
        return None
    _, path = out
    return list(reversed(path))


def admissible_envelope_vertices(target: int, h: int, d: int) -> List[Tuple[int, int]]:
    """Convenience function: (layer j, upper bound U_j)."""
    return [(j, envelope_U(target, d - j)) for j in range(d + 1)]
