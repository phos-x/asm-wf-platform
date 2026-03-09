"""
Evaluation metrics placeholder.

Implement SDR, SI-SDR, PESQ, STOI, etc. here.
"""

from __future__ import annotations
from typing import Dict, Any


def compute_metrics(ref_path: str, est_path: str) -> Dict[str, Any]:
    """
    Compute evaluation metrics between reference and estimated signals.
    """
    # TODO: implement real metrics.
    return {"dummy_metric": 0.0}
