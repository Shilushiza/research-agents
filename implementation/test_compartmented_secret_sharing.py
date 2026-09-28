import pytest

from compartmented_secret_sharing import (
    household_footprint,
    reconstruct_from_robots,
    split_by_household,
)

# 5 households, uneven robot counts, matching a realistic 1-3-robots-per-home
# fleet.
HOUSEHOLDS = {
    0: [0, 1],        # household 0: robots 0, 1
    1: [2],           # household 1: robot 2
    2: [3, 4, 5],     # household 2: robots 3, 4, 5
    3: [6],           # household 3: robot 6
    4: [7, 8],        # household 4: robots 7, 8
}
HOUSEHOLD_OF = {r: hid for hid, robots in HOUSEHOLDS.items() for r in robots}


def test_two_robots_same_household_count_as_one_vote():
    """The headline property: 2 robots from household 0 alone should NOT
    reconstruct a secret that needs tau=2 distinct households."""
    secret = 424242
    shares = split_by_household(secret, HOUSEHOLDS, tau=2)

    only_household_0 = {r: shares[r] for r in (0, 1)}
    assert household_footprint(set(only_household_0), HOUSEHOLD_OF) == 1

    # Below threshold in household terms: reconstruction runs (Shamir does
    # not itself check the threshold -- see shamir.py) but must NOT recover
    # the true secret, since only 1 distinct household's share is present.
    result = reconstruct_from_robots(only_household_0, HOUSEHOLD_OF)
    assert result != secret


def test_two_distinct_households_do_reconstruct():
    secret = 13579
    shares = split_by_household(secret, HOUSEHOLDS, tau=2)

    from_two_households = {r: shares[r] for r in (0, 2)}  # household 0 and 1
    assert household_footprint(set(from_two_households), HOUSEHOLD_OF) == 2
    assert reconstruct_from_robots(from_two_households, HOUSEHOLD_OF) == secret


def test_naive_raw_count_would_have_overcounted():
    """Demonstrates exactly the gap the mechanism closes: 3 robots from ONE
    household (raw count 3) still only count as 1 household, so they must
    NOT reconstruct a tau=2 secret -- even though a flat (t=2, N)-Shamir over
    raw robot count would have wrongly allowed 3 >= 2.
    """
    secret = 999
    shares = split_by_household(secret, HOUSEHOLDS, tau=2)
    three_robots_one_household = {r: shares[r] for r in (3, 4, 5)}  # household 2
    assert household_footprint(set(three_robots_one_household), HOUSEHOLD_OF) == 1


def test_all_households_reconstruct():
    secret = 2026
    shares = split_by_household(secret, HOUSEHOLDS, tau=3)
    one_per_household = {robots[0]: shares[robots[0]] for robots in HOUSEHOLDS.values()}
    assert reconstruct_from_robots(one_per_household, HOUSEHOLD_OF) == secret


def test_rejects_invalid_tau():
    with pytest.raises(ValueError):
        split_by_household(1, HOUSEHOLDS, tau=0)
    with pytest.raises(ValueError):
        split_by_household(1, HOUSEHOLDS, tau=len(HOUSEHOLDS) + 1)
