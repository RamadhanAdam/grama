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
