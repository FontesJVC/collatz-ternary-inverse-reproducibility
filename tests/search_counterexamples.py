"""Adversarial computational search utilities.

This script does not attempt complete theorem verification.  It deliberately looks for
small counterexamples to *overstated* variants of the theorems.
"""
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from shared.common import h_star
from paper2.paper2_core import no_wrap_bound_holds, inverse_child, xi_y


def demo_same_residual_not_same_exact_child():
    # The classic warning: residual code does not certify q=0.
    a = xi_y(1, 1)
    b = xi_y(1, 10)
    print('Residual-code warning example:')
    print(f'  Xi_1(1)  = {a}')
    print(f'  Xi_1(10) = {b}')
    print(f'  Xi_1(1) mod 9  = {a % 9}')
    print(f'  Xi_1(10) mod 9 = {b % 9}')


def demo_85_obstruction():
    x, e = inverse_child(1, 1, 1)
    print('\nNonminimal exact edge example:')
    print(f'  From y=1, t=1, q=1 gives x={x} with exponent e={e}.')
    print('  This is the exact edge 1 -> 85, absent from the q=0 skeleton.')


def table_h_star(limit=25):
    print('\nTarget-only terminal horizon h*(n) for odd n <=', limit)
    for n in range(1, limit + 1, 2):
        print(f'  n={n:2d}: h*(n)={h_star(n)} ; bound active? {no_wrap_bound_holds(n, h_star(n))}')


if __name__ == '__main__':
    demo_same_residual_not_same_exact_child()
    demo_85_obstruction()
    table_h_star(35)
