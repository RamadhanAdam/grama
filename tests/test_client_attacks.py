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
