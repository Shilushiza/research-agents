import pytest

from group_testing import build_test_groups, decode_single_defective, n_bits_for, run_tests


@pytest.mark.parametrize("n_items", [2, 3, 8, 9, 17, 100])
def test_every_item_is_uniquely_decodable(n_items):
    for defective in range(n_items):
        results = run_tests(n_items, defective)
        assert decode_single_defective(results, n_items) == defective


def test_number_of_tests_is_logarithmic():
    # 100 robots should need on the order of log2(100) ~ 7 tests, not 100.
    n_bits = n_bits_for(100)
    assert n_bits == 7


def test_group_membership_matches_bit_pattern():
    groups = build_test_groups(8)
    # item 5 = 0b101 -> should be in groups for bit 0 and bit 2, not bit 1.
    assert 5 in groups[0]
    assert 5 not in groups[1]
    assert 5 in groups[2]


def test_fewer_tests_than_naive_one_per_item():
    n_items = 1000
    n_tests = n_bits_for(n_items)
    assert n_tests < n_items  # the whole point of group testing
    assert n_tests == 10  # ceil(log2(1000)) == 10
