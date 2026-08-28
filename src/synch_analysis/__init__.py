"""
synch_analysis - Unified Synchronization Analysis Package

A unified framework for analyzing synchronization in time series data
using the Kuramoto order parameter.

Supports:
- Experimental/industrial data (Parquet files)
- Lorenz attractor simulations
- Sinusoidal signals
- Synthetic coupled oscillators (Kuramoto model)
- Belousov-Zhabotinsky oscillator (Oregonator model)
"""

from .core import SignalPair, DataSource
from .sources import (
    ParquetDataSource,
    LorenzDataSource,
    SinusoidDataSource,
    CoupledOscillatorDataSource,
    BelousovZhabotinskyDataSource,
)
from .analyzer import SynchronizationAnalyzer
from .visualizer import SynchronizationVisualizer
from .pipeline import (
    SynchronizationPipeline,
    DelayCharacterizationPipeline,
    compare_data_sources,
    export_results,
)
from .jrp import (
    lag_sweep_kuramoto,
    lag_sweep_jrp,
    compute_scores,
    find_optimal_lags,
    compute_jrp_metrics,
)

__version__ = "1.0.0"
__all__ = [
    "SignalPair",
    "DataSource",
    "ParquetDataSource",
    "LorenzDataSource",
    "SinusoidDataSource",
    "CoupledOscillatorDataSource",
    "BelousovZhabotinskyDataSource",
    "SynchronizationAnalyzer",
    "SynchronizationVisualizer",
    "SynchronizationPipeline",
    "DelayCharacterizationPipeline",
    "compare_data_sources",
    "export_results",
    "lag_sweep_kuramoto",
    "lag_sweep_jrp",
    "compute_scores",
    "find_optimal_lags",
    "compute_jrp_metrics",
]