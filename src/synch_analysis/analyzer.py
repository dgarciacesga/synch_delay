"""Core analysis engine for Kuramoto order parameter computation."""

from typing import Dict, Tuple
import numpy as np
import pandas as pd
from scipy.signal import hilbert

from .core import SignalPair


class SynchronizationAnalyzer:
    """Core analysis engine for Kuramoto order parameter computation."""

    def __init__(self, signal_pair: SignalPair):
        self.signal_pair = signal_pair
        self.hilbert_a = None
        self.hilbert_b = None
        self.phase_a = None
        self.phase_b = None
        self.amplitude_a = None
        self.amplitude_b = None
        self.order_parameter = None
        self.phase_diff = None

    def compute_hilbert_transform(self) -> Tuple[np.ndarray, np.ndarray]:
        """Compute analytic signals via Hilbert transform."""
        self.hilbert_a = hilbert(self.signal_pair.signal_a)
        self.hilbert_b = hilbert(self.signal_pair.signal_b)

        self.amplitude_a = np.abs(self.hilbert_a)
        self.amplitude_b = np.abs(self.hilbert_b)

        self.phase_a = np.angle(self.hilbert_a)
        self.phase_b = np.angle(self.hilbert_b)

        return self.hilbert_a, self.hilbert_b

    def compute_order_parameter(self) -> np.ndarray:
        """Compute Kuramoto order parameter R(t) = |<e^(iφ)>|."""
        if self.phase_a is None or self.phase_b is None:
            self.compute_hilbert_transform()

        # Complex phase vectors
        z_a = np.exp(1j * self.phase_a)
        z_b = np.exp(1j * self.phase_b)

        # Order parameter: magnitude of mean phase vector
        self.order_parameter = np.abs((z_a + z_b) / 2)
        self.phase_diff = np.angle(z_a / z_b)  # Phase difference

        return self.order_parameter

    def compute_sliding_order_parameter(self, window: int = 50) -> np.ndarray:
        """Compute sliding window order parameter."""
        if self.order_parameter is None:
            self.compute_order_parameter()

        # Moving average
        return pd.Series(self.order_parameter).rolling(window, center=True).mean().values

    def get_summary_stats(self) -> Dict[str, float]:
        """Get summary statistics."""
        if self.order_parameter is None:
            self.compute_order_parameter()

        return {
            "mean_R": float(np.mean(self.order_parameter)),
            "std_R": float(np.std(self.order_parameter)),
            "max_R": float(np.max(self.order_parameter)),
            "min_R": float(np.min(self.order_parameter)),
            "mean_phase_diff": float(np.mean(self.phase_diff)),
            "std_phase_diff": float(np.std(self.phase_diff)),
            "sync_ratio": float(np.mean(self.order_parameter > 0.8)),
        }