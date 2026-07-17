"""
synch_analysis - Unified Synchronization Analysis Package

A unified framework for analyzing synchronization in time series data
using the Kuramoto order parameter.

Supports:
- Experimental/industrial data (Parquet files)
- Lorenz attractor simulations
- Sinusoidal signals
- Synthetic coupled oscillators (Kuramoto model)
"""

from .core import SignalPair, DataSource
from .sources import (
    ParquetDataSource,
    LorenzDataSource,
    SinusoidDataSource,
    CoupledOscillatorDataSource,
)
from .analyzer import SynchronizationAnalyzer
from .visualizer import SynchronizationVisualizer
from .pipeline import SynchronizationPipeline, compare_data_sources, export_results

__version__ = "1.0.0"
__all__ = [
    "SignalPair",
    "DataSource",
    "ParquetDataSource",
    "LorenzDataSource",
    "SinusoidDataSource",
    "CoupledOscillatorDataSource",
    "SynchronizationAnalyzer",
    "SynchronizationVisualizer",
    "SynchronizationPipeline",
    "compare_data_sources",
    "export_results",
]