"""High-level pipeline for synchronization analysis."""

from typing import List, Optional, Dict, Any
import numpy as np
import pandas as pd
from pathlib import Path
import matplotlib.pyplot as plt
from matplotlib.animation import FuncAnimation

from .core import DataSource, SignalPair
from .analyzer import SynchronizationAnalyzer
from .visualizer import SynchronizationVisualizer


class SynchronizationPipeline:
    """End-to-end pipeline for synchronization analysis."""

    def __init__(self, data_source: DataSource):
        self.data_source = data_source
        self.signal_pair: Optional[SignalPair] = None
        self.analyzer: Optional[SynchronizationAnalyzer] = None
        self.visualizer: Optional[SynchronizationVisualizer] = None

    def run(self) -> "SynchronizationPipeline":
        """Execute the full pipeline."""
        print(f"Loading data: {self.data_source.get_description()}")
        self.signal_pair = self.data_source.load()
        print(f"  Signal A: {self.signal_pair.name_a} ({self.signal_pair.n_samples} samples)")
        print(f"  Signal B: {self.signal_pair.name_b} ({self.signal_pair.n_samples} samples)")

        self.analyzer = SynchronizationAnalyzer(self.signal_pair)
        self.visualizer = SynchronizationVisualizer(self.analyzer)

        print("Computing Hilbert transforms...")
        self.analyzer.compute_hilbert_transform()

        print("Computing Kuramoto order parameter...")
        self.analyzer.compute_order_parameter()

        stats = self.analyzer.get_summary_stats()
        print(f"  Mean R: {stats['mean_R']:.4f}")
        print(f"  Sync ratio (R>0.8): {stats['sync_ratio']:.2%}")

        return self

    def plot_dashboard(self, **kwargs):
        """Create and show dashboard."""
        if self.visualizer is None:
            self.run()
        return self.visualizer.create_dashboard(**kwargs)

    def animate(self, **kwargs):
        """Create phase animation."""
        if self.visualizer is None:
            self.run()
        return self.visualizer.animate_phases(**kwargs)

    def get_stats(self) -> Dict[str, float]:
        """Get analysis statistics."""
        if self.analyzer is None:
            self.run()
        return self.analyzer.get_summary_stats()


def compare_data_sources(sources: List[DataSource], labels: Optional[List[str]] = None) -> pd.DataFrame:
    """Compare synchronization across multiple data sources."""
    results = []

    for i, source in enumerate(sources):
        label = labels[i] if labels else source.get_description()
        pipeline = SynchronizationPipeline(source).run()
        stats = pipeline.get_stats()
        stats["source"] = label
        results.append(stats)

    return pd.DataFrame(results)


def export_results(pipeline: SynchronizationPipeline, output_dir: str = "results"):
    """Export analysis results to files."""
    Path(output_dir).mkdir(exist_ok=True)

    # Save statistics
    stats = pipeline.get_stats()
    pd.Series(stats).to_csv(f"{output_dir}/sync_stats.csv")

    # Save time series
    if pipeline.analyzer.order_parameter is not None:
        df = pd.DataFrame({
            "time": pipeline.analyzer.signal_pair.time[: len(pipeline.analyzer.order_parameter)],
            "R": pipeline.analyzer.order_parameter,
            "phase_diff": pipeline.analyzer.phase_diff,
            "phase_a": pipeline.analyzer.phase_a,
            "phase_b": pipeline.analyzer.phase_b,
        })
        df.to_csv(f"{output_dir}/sync_timeseries.csv", index=False)

    # Save dashboard
    fig = pipeline.plot_dashboard()
    fig.savefig(f"{output_dir}/sync_dashboard.png", dpi=150, bbox_inches="tight")
    plt.close(fig)

    print(f"Results exported to {output_dir}/")