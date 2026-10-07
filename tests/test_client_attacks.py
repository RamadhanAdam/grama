import torch
from torch.utils.data import TensorDataset

from grama.federated.client import LocalClient, label_map_for


def test_label_flip_never_keeps_a_label():
    m = label_map_for("label_flip", 6, client_id=3, seed=0)
    assert (m != torch.arange(6)).all()
    assert sorted(m.tolist()) == list(range(6))           # a permutation


def test_targeted_flip_sends_everything_to_benign():
    assert label_map_for("targeted_flip", 6, 0).tolist() == [0] * 6
    assert label_map_for(None, 6, 0) is None


def _client(attack):
    g = torch.Generator().manual_seed(0)
    ds = TensorDataset(torch.randn(40, 5, generator=g), torch.randint(0, 3, (40,), generator=g))
    return LocalClient(1, ds, batch_size=8, lr=1e-2, attack=attack, num_classes=3, poison_scale=10.0)


def test_magnitude_poison_scales_the_honest_update():
    def factory():
        torch.manual_seed(0)
        return torch.nn.Linear(5, 3)
    state = factory().state_dict()
    honest = _client(None).local_train(factory, state, local_epochs=1)
    bad = _client("magnitude_poison").local_train(factory, state, local_epochs=1)
    assert bad.malicious and not honest.malicious
    for k in honest.delta_w:
        assert torch.allclose(bad.delta_w[k], honest.delta_w[k] * 10.0, atol=1e-6)


def test_alie_sends_mean_minus_z_std_for_every_attacker():
    from grama.attacks.poisoning import alie_attack, alie_z
    from grama.federated.client import ClientUpdate
    ups = [ClientUpdate(i, {"w": torch.tensor([float(i), 2.0 * i])}, 10, 0.1) for i in range(10)]
    out = alie_attack(ups, [3, 7])
    stack = torch.stack([u.delta_w["w"] for u in ups])
    expected = stack.mean(0) - alie_z(10, 2) * stack.std(0, unbiased=False)
    assert torch.allclose(out[3].delta_w["w"], expected) and torch.allclose(out[7].delta_w["w"], expected)
    assert out[3].malicious and not out[0].malicious
    assert torch.equal(out[0].delta_w["w"], ups[0].delta_w["w"])
    assert alie_z(10, 1) == 0.0 and alie_z(10, 4) > alie_z(10, 2) > 0


def test_alie_noisy_attackers_differ_but_centre_on_the_same_vector():
    from grama.attacks.poisoning import alie_attack
    from grama.federated.client import ClientUpdate
    ups = [ClientUpdate(i, {"w": torch.randn(500) + i}, 10, 0.1) for i in range(10)]
    plain = alie_attack(ups, [3, 7])
    noisy = alie_attack(ups, [3, 7], noise=1.0, generator=torch.Generator().manual_seed(0))
    assert torch.equal(plain[3].delta_w["w"], plain[7].delta_w["w"])
    assert not torch.equal(noisy[3].delta_w["w"], noisy[7].delta_w["w"])
    assert noisy[3].malicious and noisy[7].malicious and not noisy[0].malicious
    assert (noisy[3].delta_w["w"] - plain[3].delta_w["w"]).abs().mean() > 0.1
