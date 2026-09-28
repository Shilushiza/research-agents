"""Non-adaptive binary group testing -- the combinatorial decoding primitive
behind FedGT-style malicious-client identification.

Formalized in research/tex/06_prss_he_compartmented_threshold.tex, "Направление
улучшения", citing Xhemrishi et al., FedGT, arXiv:2305.05506.

Analogy from the writeup: like pooled COVID testing -- test overlapping
groups instead of every individual, and the *pattern* of which groups come
back positive pinpoints the culprit with far fewer tests than one-per-item.

Scope, stated honestly: this implements the classic single-defective binary
ID scheme, which decodes exactly when there is exactly one defective item
among N. With multiple simultaneous defectives, the plain OR-of-bits
decoding can produce "ghost" false positives (an ID matching the observed
bit pattern without actually being defective) -- correctly handling
multiple defectives non-adaptively needs d-disjunct test matrices, which
this module does not implement. FedGT's actual malicious-client detector
(which decides whether a *federated learning aggregate* looks poisoned) is
also out of scope -- this module only provides the reusable decoding
primitive, decoupled from any specific anomaly detector.

Construction: give each of the N items (robots) an L = ceil(log2(N))-bit id.
For bit position k, the test group is {i : bit k of id(i) == 1}. A group
"tests positive" if it contains the defective item. With a single
defective, exactly the bits that are 1 in its id will test positive, so the
defective's id can be read directly off the pattern of positive tests.
"""

from __future__ import annotations

import math


def n_bits_for(n_items: int) -> int:
    if n_items < 1:
        raise ValueError("n_items must be >= 1")
    return max(1, math.ceil(math.log2(n_items)))


def build_test_groups(n_items: int) -> dict[int, set[int]]:
    """Return {bit_position: set of item ids whose id has that bit set}."""
    n_bits = n_bits_for(n_items)
    groups: dict[int, set[int]] = {k: set() for k in range(n_bits)}
    for item_id in range(n_items):
        for k in range(n_bits):
            if (item_id >> k) & 1:
                groups[k].add(item_id)
    return groups


def run_tests(n_items: int, defective_id: int) -> dict[int, bool]:
    """Simulate running the non-adaptive test battery when `defective_id`
    is the (single) defective item: a group tests positive iff it contains
    the defective.
    """
    groups = build_test_groups(n_items)
    return {k: defective_id in members for k, members in groups.items()}


def decode_single_defective(test_results: dict[int, bool], n_items: int) -> int:
    """Reconstruct the defective item's id from the pattern of positive
    tests. Only correct under the single-defective assumption -- see the
    module docstring.
    """
    n_bits = n_bits_for(n_items)
    candidate = 0
    for k in range(n_bits):
        if test_results.get(k, False):
            candidate |= (1 << k)
    if not (0 <= candidate < n_items):
        raise ValueError(
            f"decoded id {candidate} is out of range for n_items={n_items} -- "
            "the single-defective assumption was likely violated"
        )
    return candidate
