import torch

from grama.models.mamba_block import MambaBlock


def test_mamba_torch_backend_output_shape():
    B, L, D = 2, 10, 32
    block = MambaBlock(d_model=D, d_state=8, d_conv=4, expand=2, backend="torch")
    assert block.backend_used == "torch"

    x = torch.rand(B, L, D)
    y = block(x)
    assert y.shape == (B, L, D)
    assert torch.isfinite(y).all()


def test_mamba_auto_backend_falls_back_without_cuda():
    """On a machine without CUDA/mamba-ssm, 'auto' must silently use torch, not crash."""
    B, L, D = 1, 5, 16
    block = MambaBlock(d_model=D, d_state=8, d_conv=4, expand=2, backend="auto")
    x = torch.rand(B, L, D)
    y = block(x)
    assert y.shape == (B, L, D)


def test_mamba_gradients_flow():
    """Sanity check the selective-scan recurrence is actually differentiable end-to-end."""
    B, L, D = 1, 6, 16
    block = MambaBlock(d_model=D, d_state=4, d_conv=3, expand=2, backend="torch")
    x = torch.rand(B, L, D, requires_grad=True)
    y = block(x)
    y.sum().backward()
    assert x.grad is not None
    assert torch.isfinite(x.grad).all()
