"""Baseline: 1D-CNN + BiGRU + Attention + AWI aggregation (Mnkash et al., 2026).

Implements the prior architecture (Sec 2.1) so the GraMa framework has a
real, same-codebase point of comparison for Table 1 / Sec 6.2.1's baseline
comparison, rather than only citing the paper's own reported numbers.

NOT YET IMPLEMENTED — this is a placeholder documenting the intended
structure so the comparison is planned before GraMa itself is fully trained.
Building it out means mirroring src/grama/models/ and src/grama/federated/
with baseline-specific counterparts:
    src/grama/baselines/cnn_bigru_encoder.py   (Sec 2.1: 1D-CNN + BiGRU + attention)
    src/grama/baselines/awi_aggregator.py       (eq. 1-2: AWI + dual-threshold defense)
then reusing the same LocalClient / FederatedServer loop with these swapped in,
so both architectures share identical data splits, client sampling, and
adversarial simulation for a fair comparison.
"""
from __future__ import annotations

import sys

if __name__ == "__main__":
    print(__doc__)
    sys.exit(0)
