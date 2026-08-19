"""Temporal Sequence Mamba SSM block (Sec 5.2, eq. 7-10).

Two backends behind one interface:
  - "cuda":  wraps the official `mamba-ssm` package's fused selective-scan
             kernel. Fast, but only installs/runs on a CUDA GPU with a
             matching toolkit (e.g. Kinesis Network A100 nodes).
  - "torch": a plain sequential PyTorch implementation of the same
             recurrence (eq. 9-10), correct but O(L) in Python loop overhead.
             Portable — runs anywhere torch runs, used for local/CPU dev,
             unit tests, and as a safety net if the CUDA kernel is
             unavailable at runtime.

`backend="auto"` (default, see config/model.yaml) tries cuda first and
transparently falls back to torch, logging which one was actually used.
"""
from __future__ import annotations

import math

import torch
import torch.nn as nn
import torch.nn.functional as F

from grama.utils.logging import get_logger

logger = get_logger(__name__)


def _cuda_mamba_available() -> bool:
    if not torch.cuda.is_available():
        return False
    try:
        import mamba_ssm  # noqa: F401
    except ImportError:
        return False
    return True


class _PureTorchSelectiveScan(nn.Module):
    """Direct implementation of eq. 7-10: discretized selective SSM recurrence.

    This intentionally mirrors the math in the concept note rather than
    chasing throughput: A is a learned (d_model, d_state) log-parameter,
    B_t/C_t/delta_t are input-dependent (the "selection mechanism", eq. 9),
    and the discrete recurrence h_t = A_bar_t h_{t-1} + B_bar_t x_t,
    y_t = C_t h_t is unrolled explicitly over the sequence (eq. 10).
    """

    def __init__(self, d_model: int, d_state: int = 16, d_conv: int = 4, expand: int = 2, dt_rank: int | str = "auto"):
        super().__init__()
        self.d_model = d_model
        self.d_state = d_state
        self.d_inner = expand * d_model
        self.dt_rank = math.ceil(d_model / 16) if dt_rank == "auto" else int(dt_rank)

        self.in_proj = nn.Linear(d_model, 2 * self.d_inner)
        self.conv1d = nn.Conv1d(
            self.d_inner, self.d_inner, kernel_size=d_conv, groups=self.d_inner, padding=d_conv - 1
        )
        # Selection mechanism (eq. 9): B_t, C_t, delta_t as functions of x_t.
        self.x_proj = nn.Linear(self.d_inner, self.dt_rank + 2 * self.d_state)
        self.dt_proj = nn.Linear(self.dt_rank, self.d_inner)

        # A: (d_inner, d_state), stored in log-space and kept negative via -exp() for stability.
        A = torch.arange(1, d_state + 1, dtype=torch.float32).repeat(self.d_inner, 1)
        self.A_log = nn.Parameter(torch.log(A))
        self.D = nn.Parameter(torch.ones(self.d_inner))

        self.out_proj = nn.Linear(self.d_inner, d_model)

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        """x: (B, L, d_model) -> (B, L, d_model)"""
        B, L, _ = x.shape
        xz = self.in_proj(x)  # (B, L, 2*d_inner)
        x_in, z = xz.chunk(2, dim=-1)

        x_in = x_in.transpose(1, 2)  # (B, d_inner, L)
        x_in = self.conv1d(x_in)[..., :L]
        x_in = F.silu(x_in).transpose(1, 2)  # (B, L, d_inner)

        x_dbl = self.x_proj(x_in)  # (B, L, dt_rank + 2*d_state)
        dt, B_t, C_t = torch.split(x_dbl, [self.dt_rank, self.d_state, self.d_state], dim=-1)
        delta = F.softplus(self.dt_proj(dt))  # eq. 9: Δ_t = softplus(...)  -> (B, L, d_inner)

        A = -torch.exp(self.A_log)  # (d_inner, d_state), negative for stable decay

        # Discretize per-timestep (eq. 8, applied with input-dependent Δ_t / B_t from eq. 9).
        # A_bar_t: (B, L, d_inner, d_state) — expensive but explicit/correct.
        delta_A = torch.einsum("bld,dn->bldn", delta, A)
        A_bar = torch.exp(delta_A)
        B_bar = torch.einsum("bld,bln->bldn", delta, B_t)

        h = torch.zeros(B, self.d_inner, self.d_state, device=x.device, dtype=x.dtype)
        ys = []
        for t in range(L):
            # eq. 10: h_t = A_bar_t h_{t-1} + B_bar_t x_t
            h = A_bar[:, t] * h + B_bar[:, t] * x_in[:, t].unsqueeze(-1)
            # eq. 10: y_t = C_t h_t
            y_t = torch.einsum("bdn,bn->bd", h, C_t[:, t])
            ys.append(y_t)
        y = torch.stack(ys, dim=1)  # (B, L, d_inner)
        y = y + x_in * self.D  # skip connection (analogous to D in eq. 7)

        y = y * F.silu(z)  # gating
        return self.out_proj(y)


class _CudaMambaWrapper(nn.Module):
    """Thin wrapper around the official mamba-ssm fused kernel."""

    def __init__(self, d_model: int, d_state: int = 16, d_conv: int = 4, expand: int = 2, **_ignored):
        super().__init__()
        from mamba_ssm import Mamba  # deferred import — only reached if CUDA backend selected

        self.mamba = Mamba(d_model=d_model, d_state=d_state, d_conv=d_conv, expand=expand)

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        return self.mamba(x)


class MambaBlock(nn.Module):
    """Public interface: picks cuda or torch backend per config, exposes forward(x)."""

    def __init__(
        self,
        d_model: int,
        d_state: int = 16,
        d_conv: int = 4,
        expand: int = 2,
        dt_rank: int | str = "auto",
        backend: str = "auto",
    ):
        super().__init__()
        use_cuda = backend == "cuda" or (backend == "auto" and _cuda_mamba_available())

        if use_cuda and not _cuda_mamba_available():
            logger.warning("backend='cuda' requested but mamba-ssm/CUDA unavailable — falling back to torch.")
            use_cuda = False

        if use_cuda:
            logger.info("MambaBlock: using CUDA fused kernel (mamba-ssm).")
            self.impl = _CudaMambaWrapper(d_model, d_state, d_conv, expand)
            self.backend_used = "cuda"
        else:
            logger.info("MambaBlock: using pure-PyTorch selective-scan fallback.")
            self.impl = _PureTorchSelectiveScan(d_model, d_state, d_conv, expand, dt_rank)
            self.backend_used = "torch"

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        """x: (B, L, d_model) sequence of per-window topological embeddings -> (B, L, d_model)"""
        return self.impl(x)
