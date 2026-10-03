import torch

from grama.models.gat_encoder import SpatialTopologicalGAT, GATLayer


def test_gat_layer_output_shape():
    B, N, F_in, F_out, heads = 2, 5, 8, 4, 3
    layer = GATLayer(F_in, F_out, num_heads=heads, concat_heads=True)
    x = torch.rand(B, N, F_in)
    adj = torch.ones(B, N, N)  # fully connected, incl. self-loops

    out = layer(x, adj)
    assert out.shape == (B, N, F_out * heads)
    assert torch.isfinite(out).all()


def test_gat_layer_respects_adjacency_mask():
    """A node with zero edges (isolated) should not crash and shouldn't blow up to NaN/Inf."""
    B, N, F_in, F_out = 1, 4, 6, 4
    layer = GATLayer(F_in, F_out, num_heads=2, concat_heads=False)
    x = torch.rand(B, N, F_in)
    adj = torch.zeros(B, N, N)
    adj[0, 0, 0] = 1.0  # only node 0 has a self-loop; nodes 1-3 fully isolated

    out = layer(x, adj)
    assert torch.isfinite(out).all()


def test_spatial_topological_gat_end_to_end_shape():
    B, N, F_in = 2, 6, 11
    gat = SpatialTopologicalGAT(
        in_features=F_in, hidden_features=16, out_features=32, num_heads=4,
    )
    x = torch.rand(B, N, F_in)
    adj = torch.ones(B, N, N)

    z = gat(x, adj)
    assert z.shape == (B, N, 32)

    token = gat.pool_to_sequence_token(z)
    assert token.shape == (B, 32)


def test_split_attention_matches_concatenated_form():
    """a^T [Wx_i || Wx_j] computed as two dot products must equal the concatenated form of eq. 4."""
    torch.manual_seed(0)
    layer = GATLayer(6, 5, num_heads=2, concat_heads=True, dropout=0.0)
    x = torch.rand(3, 4, 6)
    adj = torch.ones(3, 4, 4)
    Wx = torch.einsum("bnf,hfo->bhno", x, layer.W)
    pairs = torch.cat([Wx.unsqueeze(3).expand(-1, -1, -1, 4, -1), Wx.unsqueeze(2).expand(-1, -1, 4, -1, -1)], -1)
    e = layer.leaky_relu(torch.einsum("bhijf,hf->bhij", pairs, layer.a))
    alpha = torch.softmax(e, dim=-1)
    expected = torch.einsum("bhij,bhjo->bhio", alpha, Wx).permute(0, 2, 1, 3).reshape(3, 4, 10)
    assert torch.allclose(layer(x, adj), expected, atol=1e-6)


def test_pooling_ignores_inactive_nodes():
    gat = SpatialTopologicalGAT(in_features=3, hidden_features=4, out_features=4, num_heads=1, pooling="mean")
    z = torch.tensor([[[1.0] * 4, [3.0] * 4, [100.0] * 4]])
    adj = torch.diag(torch.tensor([1.0, 1.0, 0.0])).unsqueeze(0)  # node 2 silent
    assert torch.allclose(gat.pool_to_sequence_token(z, adj), torch.full((1, 4), 2.0))
