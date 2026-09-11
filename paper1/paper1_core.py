"""Minimal-q residual skeleton helpers (Paper 1)."""
from __future__ import annotations

from typing import Dict, List, Set, Tuple
from shared.common import D, INTERIOR_T


def b_t_from_unit(y: int, t: int) -> int:
    if y % 3 == 0:
        raise ValueError("y must be a unit modulo 3")
    target = (1 + 3 * t) % 9
    yy = y % 9
    for b in range(1, 7):
        if (pow(2, b, 9) * yy) % 9 == target:
            return b
    raise AssertionError("No base exponent found")


def phi_min(h: int, r: int, k: int, t: int) -> int:
    """Minimal residual transition Phi_h^min(r;k,t) modulo 3^(2h)."""
    M = 3 ** (2 * h)
    rho = r % M
    if rho % 3 == 0:
        raise ValueError("r must be a unit class")
    Y = rho + k * M
    b = b_t_from_unit(rho, t)
    num = pow(2, b) * Y - 1
    assert num % 3 == 0
    return (num // 3) % M


def interior_states(h: int) -> List[int]:
    M = 3 ** (2 * h)
    return [r for r in range(M) if r % 3 != 0]


def minimal_graph(h: int) -> Dict[int, Set[int]]:
    """Directed graph on interior unit classes only."""
    G: Dict[int, Set[int]] = {r: set() for r in interior_states(h)}
    for r in G:
        for k in D:
            for t in INTERIOR_T:
                G[r].add(phi_min(h, r, k, t))
    return G


def indegrees(G: Dict[int, Set[int]]) -> Dict[int, int]:
    indeg = {v: 0 for v in G}
    for u, nbrs in G.items():
        for v in nbrs:
            indeg[v] += 1
    return indeg


def is_strongly_connected(G: Dict[int, Set[int]]) -> bool:
    if not G:
        return True
    start = next(iter(G))
    def dfs(graph, s):
        seen = set()
        stack = [s]
        while stack:
            u = stack.pop()
            if u in seen:
                continue
            seen.add(u)
            stack.extend(graph[u] - seen)
        return seen
    seen1 = dfs(G, start)
    if len(seen1) != len(G):
        return False
    RG = {u: set() for u in G}
    for u, nbrs in G.items():
        for v in nbrs:
            RG[v].add(u)
    seen2 = dfs(RG, start)
    return len(seen2) == len(G)
