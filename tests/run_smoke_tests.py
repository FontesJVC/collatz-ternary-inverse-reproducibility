from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from shared.common import h_star
from paper1.paper1_core import minimal_graph, indegrees, is_strongly_connected
from paper2.paper2_core import valuation_isometry_holds, smallest_uniform_terminal_horizon, forward_exact_path_from_one

print('Running smoke tests...')

# Paper 1 small graph checks
G1 = minimal_graph(1)
assert len(G1) == 6, f"Expected 6 interior states at h=1, got {len(G1)}"
indeg = indegrees(G1)
outdeg_values = {len(v) for v in G1.values()}
assert outdeg_values == {6}, f"Expected out-degree 6 everywhere, got {outdeg_values}"
assert set(indeg.values()) == {6}, f"Expected in-degree 6 everywhere, got {set(indeg.values())}"
assert is_strongly_connected(G1), 'Expected h=1 minimal graph to be strongly connected'

# Paper 2 edge-fiber isometry check on a small range
for y in (1,5,7,11,13):
    assert valuation_isometry_holds(y, 20), f"valuation isometry failed for y={y}"

# Target-only horizon examples
assert smallest_uniform_terminal_horizon(35) == h_star(35) == 4
assert smallest_uniform_terminal_horizon(27) == h_star(27) == 4

# Example path 1 -> 5 -> 53 -> 35 (reverse reduced odd trajectory of 35)
path35 = forward_exact_path_from_one(35)
assert path35 == [1,5,53,35], path35

print('All smoke tests passed.')
