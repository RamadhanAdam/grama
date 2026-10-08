import pytest
import torch

from grama.models.baselines_extra import GCNWindowIDS, TransformerIDS

B, L, N, F, W, C = 3, 4, 7, 10, 16, 5


def graph_batch():
    x = torch.randn(B, L, N, F)
    active = torch.rand(B, L, N) > 0.3
    x[..., -2] = active.float()
    adj = (active.unsqueeze(-1) & active.unsqueeze(-2)).float()
    return x, adj


@pytest.mark.parametrize("temporal", ["last", "gru"])
def test_gcn_shapes_and_gradients(temporal):
    model = GCNWindowIDS(F, N, C, hidden_features=16, temporal=temporal)
    x, adj = graph_batch()
    out = model(x, adj)
    assert out.shape == (B, C)
    out.sum().backward()
    assert all(p.grad is not None for p in model.parameters())


def test_gcn_last_window_ignores_the_earlier_windows():
    model = GCNWindowIDS(F, N, C, hidden_features=16, temporal="last").eval()
    x, adj = graph_batch()
    other = x.clone()
    other[:, :-1] = torch.randn_like(other[:, :-1])
    assert torch.allclose(model(x, adj), model(other, adj), atol=1e-6)


def test_gcn_gru_reads_the_earlier_windows():
    model = GCNWindowIDS(F, N, C, hidden_features=16, temporal="gru").eval()
    x, adj = graph_batch()
    other = x.clone()
    other[:, 0] = torch.randn_like(other[:, 0])
    assert not torch.allclose(model(x, adj), model(other, adj), atol=1e-6)


def test_gcn_survives_a_window_with_no_active_node():
    model = GCNWindowIDS(F, N, C, hidden_features=16).eval()
    x = torch.randn(B, L, N, F)
    out = model(x, torch.zeros(B, L, N, N))
    assert torch.isfinite(out).all()


def test_transformer_shapes_and_gradients():
    model = TransformerIDS(num_nodes=N, num_classes=C, d_model=16, heads=2, seq_len=L)
    ids = torch.randint(0, N, (B, L, W))
    payload = torch.rand(B, L, W, 8)
    out = model(ids, payload)
    assert out.shape == (B, C)
    out.sum().backward()
    assert all(p.grad is not None for p in model.parameters())


def test_transformer_sees_the_order_of_windows():
    model = TransformerIDS(num_nodes=N, num_classes=C, d_model=16, heads=2, seq_len=L).eval()
    ids = torch.randint(0, N, (B, L, W))
    payload = torch.rand(B, L, W, 8)
    assert not torch.allclose(model(ids, payload), model(ids.flip(1), payload.flip(1)), atol=1e-6)


def test_invalid_temporal_is_rejected():
    with pytest.raises(ValueError):
        GCNWindowIDS(F, N, C, temporal="mamba")
