"""Core data structures and base classes."""

from dataclasses import dataclass
from abc import ABC, abstractmethod
from typing import Optional, Dict, Any
import numpy as np


@dataclass
class SignalPair:
    """Container for two signals to analyze for synchronization."""

    signal_a: np.ndarray
    signal_b: np.ndarray
    time: Optional[np.ndarray] = None
    name_a: str = "Signal A"
    name_b: str = "Signal B"
    sampling_rate: float = 1.0

    def __post_init__(self):
        if self.time is None:
            self.time = np.arange(len(self.signal_a)) / self.sampling_rate
        assert len(self.signal_a) == len(self.signal_b), "Signals must have same length"

    @property
    def n_samples(self) -> int:
        return len(self.signal_a)


class DataSource(ABC):
    """Abstract base class for data sources."""

    @abstractmethod
    def load(self) -> SignalPair:
        """Load and return a SignalPair for analysis."""
        pass

    @abstractmethod
    def get_description(self) -> str:
        """Return a human-readable description of the data source."""
        pass