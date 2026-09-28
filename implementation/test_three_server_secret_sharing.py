"""Unit tests for three_server_secret_sharing.py.

Run with: python -m pytest test_three_server_secret_sharing.py -v
"""

import random

import pytest

from three_server_secret_sharing import (
    MODULUS,
    Server,
    reveal,
    run_protocol,
    split_secret,
)


def test_split_secret_reconstructs_correctly():
    for x in [0, 1, 500, MODULUS - 1]:
        s1, s2, s3 = split_secret(x)
        assert (s1 + s2 + s3) % MODULUS == x


def test_split_secret_rejects_out_of_range():
    with pytest.raises(ValueError):
        split_secret(-1)
    with pytest.raises(ValueError):
        split_secret(MODULUS)


def test_single_robot_roundtrip():
    assert run_protocol([42]) == 42


def test_many_robots_matches_plain_sum():
    random.seed(1)
    values = [random.randint(0, 10_000) for _ in range(50)]
    assert run_protocol(values) == sum(values) % MODULUS


def test_zero_robots_sums_to_zero():
    assert run_protocol([]) == 0


def test_reveal_requires_exactly_three_servers():
    servers = [Server(0), Server(1)]
    with pytest.raises(ValueError):
        reveal(servers)


def test_no_single_server_partial_sum_equals_true_sum():
    """The whole point of the scheme: after running the protocol on a
    non-trivial input, no individual server's partial_sum should equal the
    true aggregate -- only the combination of all 3 does.
    """
    random.seed(2)
    values = [random.randint(1, 1000) for _ in range(20)]
    true_sum = sum(values) % MODULUS

    servers = [Server(server_id=i) for i in range(3)]
    for x in values:
        shares = split_secret(x)
        for server, share in zip(servers, shares):
            server.receive_share(share)

    for s in servers:
        assert s.partial_sum != true_sum
    assert reveal(servers) == true_sum


def test_wrong_share_count_still_reconstructs_if_shares_match_secret():
    """Sanity check on the arithmetic itself, independent of the Server class:
    any 3 numbers that sum to x mod p are a valid sharing of x.
    """
    x = 777
    s1, s2, s3 = split_secret(x)
    assert (s1 + s2 + s3) % MODULUS == x
    # shares are (with overwhelming probability) not trivially equal to x
    assert s1 != x and s2 != x and s3 != x
