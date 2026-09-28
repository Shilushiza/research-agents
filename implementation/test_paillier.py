import random

import pytest

from paillier import keygen


def test_encrypt_decrypt_roundtrip():
    kp = keygen(bits=128)
    for m in [0, 1, 42, kp.public.n - 1]:
        c = kp.public.encrypt(m)
        assert kp.private.decrypt(c) == m


def test_ciphertexts_are_randomized():
    kp = keygen(bits=128)
    c1 = kp.public.encrypt(123)
    c2 = kp.public.encrypt(123)
    assert c1 != c2  # different random r -> different ciphertext
    assert kp.private.decrypt(c1) == kp.private.decrypt(c2) == 123


def test_homomorphic_addition():
    kp = keygen(bits=128)
    random.seed(0)
    values = [random.randint(0, 1000) for _ in range(8)]
    ciphertexts = [kp.public.encrypt(v) for v in values]

    acc = kp.public.encrypt(0)
    for c in ciphertexts:
        acc = kp.public.add(acc, c)

    assert kp.private.decrypt(acc) == sum(values) % kp.public.n


def test_rejects_plaintext_out_of_range():
    kp = keygen(bits=128)
    with pytest.raises(ValueError):
        kp.public.encrypt(-1)
    with pytest.raises(ValueError):
        kp.public.encrypt(kp.public.n)
