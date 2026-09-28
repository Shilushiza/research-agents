import random

import pytest

from shamir import DEFAULT_PRIME, reconstruct, split


def test_roundtrip_exact_threshold():
    secret = 123456789
    shares = split(secret, t=3, n=5)
    assert reconstruct(shares[:3]) == secret


def test_roundtrip_different_subsets_agree():
    secret = 42
    shares = split(secret, t=3, n=6)
    random.seed(0)
    for _ in range(10):
        subset = random.sample(shares, 3)
        assert reconstruct(subset) == secret


def test_all_shares_also_reconstruct():
    secret = 999
    shares = split(secret, t=2, n=7)
    assert reconstruct(shares) == secret


def test_below_threshold_gives_no_reliable_answer():
    """t-1 shares should not (in general) reconstruct the true secret --
    this is a sanity check, not a formal secrecy proof."""
    secret = 777
    shares = split(secret, t=4, n=6)
    wrong = reconstruct(shares[:3])
    assert wrong != secret


def test_rejects_invalid_threshold():
    with pytest.raises(ValueError):
        split(5, t=0, n=3)
    with pytest.raises(ValueError):
        split(5, t=4, n=3)


def test_rejects_secret_out_of_range():
    with pytest.raises(ValueError):
        split(-1, t=2, n=3)
    with pytest.raises(ValueError):
        split(DEFAULT_PRIME, t=2, n=3)


def test_large_secret_near_prime_boundary():
    secret = DEFAULT_PRIME - 1
    shares = split(secret, t=3, n=5)
    assert reconstruct(shares[:3]) == secret
