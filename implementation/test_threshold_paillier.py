import random

import pytest

from paillier import keygen
from threshold_paillier import deal_shares, threshold_decrypt


def test_threshold_decrypt_matches_plain_decrypt():
    kp = keygen(bits=128)
    servers = deal_shares(kp.private, n_servers=3)

    for m in [0, 1, 42, kp.public.n - 1]:
        c = kp.public.encrypt(m)
        assert threshold_decrypt(c, servers) == m


def test_no_single_server_share_equals_the_secrets():
    kp = keygen(bits=128)
    servers = deal_shares(kp.private, n_servers=4)
    for s in servers:
        assert s.lambda_share != kp.private.lam
        assert s.mu_share != kp.private.mu


def test_lambda_shares_sum_exactly_to_lambda():
    kp = keygen(bits=128)
    servers = deal_shares(kp.private, n_servers=5)
    assert sum(s.lambda_share for s in servers) == kp.private.lam


def test_mu_shares_sum_to_mu_mod_n():
    kp = keygen(bits=128)
    servers = deal_shares(kp.private, n_servers=5)
    assert sum(s.mu_share for s in servers) % kp.public.n == kp.private.mu


def test_homomorphic_add_then_threshold_decrypt():
    kp = keygen(bits=128)
    servers = deal_shares(kp.private, n_servers=3)
    random.seed(0)
    values = [random.randint(0, 1000) for _ in range(6)]

    acc = kp.public.encrypt(0)
    for v in values:
        acc = kp.public.add(acc, kp.public.encrypt(v))

    assert threshold_decrypt(acc, servers) == sum(values) % kp.public.n


def test_missing_one_server_breaks_n_of_n_reconstruction():
    """This is the honestly-documented limitation: N-of-N needs all servers.
    Dropping one should not silently produce the right answer."""
    kp = keygen(bits=128)
    servers = deal_shares(kp.private, n_servers=4)
    c = kp.public.encrypt(777)
    assert threshold_decrypt(c, servers[:3]) != 777


def test_rejects_too_few_servers():
    kp = keygen(bits=128)
    servers = deal_shares(kp.private, n_servers=3)
    with pytest.raises(ValueError):
        threshold_decrypt(kp.public.encrypt(1), servers[:1])
