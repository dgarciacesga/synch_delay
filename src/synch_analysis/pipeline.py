"""High-level pipeline for synchronization analysis."""

from typing import List, Optional, Dict, Any, Tuple
import numpy as np
import pandas as pd
from pathlib import Path
import matplotlib.pyplot as plt
from matplotlib.animation import FuncAnimation

from .core import DataSource, SignalPair
from .analyzer import SynchronizationAnalyzer
from .visualizer import SynchronizationVisualizer
from .jrp import (
    lag_sweep_kuramoto,
    lag_sweep_jrp,
    compute_scores,
    find_optimal_lags,
    compute_jrp_metrics,
)


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


def compare_data_sources(
    sources: List[DataSource], labels: Optional[List[str]] = None
) -> pd.DataFrame:
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
        df = pd.DataFrame(
            {
                "time": pipeline.analyzer.signal_pair.time[
                    : len(pipeline.analyzer.order_parameter)
                ],
                "R": pipeline.analyzer.order_parameter,
                "phase_diff": pipeline.analyzer.phase_diff,
                "phase_a": pipeline.analyzer.phase_a,
                "phase_b": pipeline.analyzer.phase_b,
            }
        )
        df.to_csv(f"{output_dir}/sync_timeseries.csv", index=False)

    # Save dashboard
    fig = pipeline.plot_dashboard()
    fig.savefig(f"{output_dir}/sync_dashboard.png", dpi=150, bbox_inches="tight")
    plt.close(fig)

    print(f"Results exported to {output_dir}/")


class DelayCharacterizationPipeline:
    """Pipeline for delay characterization via lag sweep (Kuramoto + JRP)."""

    def __init__(
        self,
        data_source: DataSource,
        max_lag: int = 100,
        lag_step: int = 1,
        jrp_m: int = 3,
        jrp_tau: int = 1,
        jrp_rate: float = 0.05,
        jrp_smooth_size: int = 5,
    ):
        self.data_source = data_source
        self.max_lag = max_lag
        self.lag_step = lag_step
        self.jrp_m = jrp_m
        self.jrp_tau = jrp_tau
        self.jrp_rate = jrp_rate
        self.jrp_smooth_size = jrp_smooth_size

        self.signal_pair: Optional[SignalPair] = None
        self.lags: Optional[np.ndarray] = None
        self.kuramoto_results: Optional[pd.DataFrame] = None
        self.jrp_results: Optional[pd.DataFrame] = None
        self.combined_results: Optional[pd.DataFrame] = None
        self.optimal_lags: Optional[Dict[str, int]] = None

    def run(self) -> "DelayCharacterizationPipeline":
        """Execute the full delay characterization pipeline."""
        print(f"Loading data: {self.data_source.get_description()}")
        self.signal_pair = self.data_source.load()
        print(f"  Signal A: {self.signal_pair.name_a} ({self.signal_pair.n_samples} samples)")
        print(f"  Signal B: {self.signal_pair.name_b} ({self.signal_pair.n_samples} samples)")

        # Define lag range
        self.lags = np.arange(-self.max_lag, self.max_lag + 1, self.lag_step)

        # Kuramoto lag sweep
        print(f"Running Kuramoto lag sweep (lags: {len(self.lags)})...")
        self.kuramoto_results = lag_sweep_kuramoto(
            self.signal_pair.signal_a,
            self.signal_pair.signal_b,
            self.lags,
            self.signal_pair.sampling_rate,
        )

        # JRP lag sweep
        print(f"Running JRP lag sweep...")
        self.jrp_results = lag_sweep_jrp(
            self.signal_pair.signal_a,
            self.signal_pair.signal_b,
            self.lags,
            m=self.jrp_m,
            tau=self.jrp_tau,
            rate=self.jrp_rate,
            smooth_size=self.jrp_smooth_size,
            sampling_rate=self.signal_pair.sampling_rate,
        )

        # Combine and score
        print("Computing combined scores...")
        self.combined_results = compute_scores(
            self.kuramoto_results,
            self.jrp_results,
            self.max_lag,
        )

        # Find optimal lags
        self.optimal_lags = find_optimal_lags(self.combined_results, self.max_lag)

        # Print summary
        print(
            f"  Best Kuramoto lag: {self.optimal_lags['best_kuramoto_lag']} steps ({self.optimal_lags['best_kuramoto_lag'] / self.signal_pair.sampling_rate:.3f}s)"
        )
        print(
            f"  Best JRP lag: {self.optimal_lags['best_jrp_lag']} steps ({self.optimal_lags['best_jrp_lag'] / self.signal_pair.sampling_rate:.3f}s)"
        )
        print(
            f"  Best Combined lag: {self.optimal_lags['best_combined_lag']} steps ({self.optimal_lags['best_combined_lag'] / self.signal_pair.sampling_rate:.3f}s)"
        )

        return self

    def get_results(self) -> pd.DataFrame:
        """Get combined lag sweep results."""
        if self.combined_results is None:
            self.run()
        return self.combined_results

    def get_optimal_lags(self) -> Dict[str, int]:
        """Get optimal lags from both methods."""
        if self.optimal_lags is None:
            self.run()
        return self.optimal_lags

    def plot_kuramoto(self, **kwargs):
        """Plot Kuramoto metrics vs lag."""
        if self.kuramoto_results is None:
            self.run()

        fig, axes = plt.subplots(2, 2, figsize=(14, 10))
        fig.patch.set_facecolor("white")

        df = self.kuramoto_results
        # Add score from combined results
        if self.combined_results is not None:
            df = df.merge(self.combined_results[["lag", "kuramoto_score"]], on="lag", how="left")

        true_delay_sec = kwargs.get("true_delay_sec", None)

        axes[0, 0].plot(df["lag_sec"], df["r_mean"], "b-", linewidth=1)
        axes[0, 0].set_xlabel("Lag (seconds)")
        axes[0, 0].set_ylabel("Mean Kuramoto r")
        axes[0, 0].set_title("Mean Kuramoto Order Parameter vs Lag")
        axes[0, 0].grid(False)
        if true_delay_sec is not None:
            axes[0, 0].axvline(
                x=true_delay_sec,
                color="r",
                linestyle="--",
                alpha=0.7,
                label=f"True delay ({true_delay_sec:.2f}s)",
            )
            axes[0, 0].legend()

        axes[0, 1].plot(df["lag_sec"], df["frac_above_07"], "r-", linewidth=1)
        axes[0, 1].set_xlabel("Lag (seconds)")
        axes[0, 1].set_ylabel("Fraction R > 0.7")
        axes[0, 1].set_title("Fraction Above Threshold vs Lag")
        axes[0, 1].grid(False)

        axes[1, 0].plot(df["lag_sec"], df["max_sustained_sec"], "g-", linewidth=1)
        axes[1, 0].set_xlabel("Lag (seconds)")
        axes[1, 0].set_ylabel("Max Sustained (s)")
        axes[1, 0].set_title("Max Sustained Synchronization vs Lag")
        axes[1, 0].grid(False)

        if "kuramoto_score" in df.columns:
            axes[1, 1].plot(df["lag_sec"], df["kuramoto_score"], "k-", linewidth=1)
            axes[1, 1].set_xlabel("Lag (seconds)")
            axes[1, 1].set_ylabel("Kuramoto Score")
            axes[1, 1].set_title("Kuramoto Score (normalized frac × r_mean)")
            axes[1, 1].grid(False)

        plt.tight_layout()
        return fig

    def plot_jrp(self, **kwargs):
        """Plot JRP metrics vs lag."""
        if self.jrp_results is None:
            self.run()

        jrp_df = self.jrp_results[self.jrp_results["jrp_RR"] > 0].copy()
        if len(jrp_df) == 0:
            print("No valid JRP results to plot")
            return None

        # Add score from combined results
        if self.combined_results is not None:
            jrp_df = jrp_df.merge(self.combined_results[["lag", "jrp_score"]], on="lag", how="left")

        true_delay_sec = kwargs.get("true_delay_sec", None)

        fig, axes = plt.subplots(2, 2, figsize=(14, 10))
        fig.patch.set_facecolor("white")

        axes[0, 0].plot(jrp_df["lag_sec"], jrp_df["jrp_RR"], "b-o", linewidth=1, markersize=3)
        axes[0, 0].set_xlabel("Lag (seconds)")
        axes[0, 0].set_ylabel("Joint Recurrence Rate")
        axes[0, 0].set_title("JRP: Recurrence Rate vs Lag")
        axes[0, 0].grid(False)
        if true_delay_sec is not None:
            axes[0, 0].axvline(x=true_delay_sec, color="r", linestyle="--", alpha=0.7, label=f"True delay ({true_delay_sec:.2f}s)")
            axes[0, 0].legend()

        axes[0, 1].plot(jrp_df["lag_sec"], jrp_df["jrp_DET"], "r-o", linewidth=1, markersize=3)
        axes[0, 1].set_xlabel("Lag (seconds)")
        axes[0, 1].set_ylabel("Determinism")
        axes[0, 1].set_title("JRP: Determinism vs Lag")
        axes[0, 1].grid(False)

        axes[1, 0].plot(jrp_df["lag_sec"], jrp_df["jrp_LAM"], "g-o", linewidth=1, markersize=3)
        axes[1, 0].set_xlabel("Lag (seconds)")
        axes[1, 0].set_ylabel("Laminarity")
        axes[1, 0].set_title("JRP: Laminarity vs Lag")
        axes[1, 0].grid(False)

        if "jrp_score" in jrp_df.columns:
            axes[1, 1].plot(jrp_df["lag_sec"], jrp_df["jrp_score"], "k-o", linewidth=1, markersize=3)
            axes[1, 1].set_xlabel("Lag (seconds)")
            axes[1, 1].set_ylabel("JRP Score (norm RR)")
            axes[1, 1].set_title("JRP Score vs Lag")
            axes[1, 1].grid(False)

        plt.tight_layout()
        return fig

    def plot_combined(self, **kwargs):
        """Plot combined Kuramoto + JRP scores."""
        if self.combined_results is None:
            self.run()

        df = self.combined_results

        fig, axes = plt.subplots(2, 2, figsize=(14, 10))
        fig.patch.set_facecolor("white")

        axes[0, 0].plot(df["lag_sec"], df["kuramoto_score"], "b-", linewidth=1, label="Kuramoto")
        axes[0, 0].set_xlabel("Lag (seconds)")
        axes[0, 0].set_ylabel("Score")
        axes[0, 0].set_title("Kuramoto Score vs Lag")
        axes[0, 0].grid(False)
        axes[0, 0].legend()

        axes[0, 1].plot(df["lag_sec"], df["jrp_score"], "r-", linewidth=1, label="JRP")
        axes[0, 1].set_xlabel("Lag (seconds)")
        axes[0, 1].set_ylabel("Score")
        axes[0, 1].set_title("JRP Score vs Lag")
        axes[0, 1].grid(False)
        axes[0, 1].legend()

        axes[1, 0].plot(df["lag_sec"], df["combined_score"], "k-", linewidth=2, label="Combined")
        axes[1, 0].set_xlabel("Lag (seconds)")
        axes[1, 0].set_ylabel("Score")
        axes[1, 0].set_title("Combined Score (mean of normalized)")
        axes[1, 0].grid(False)
        axes[1, 0].legend()

        # Mark optimal lags (convert to seconds)
        opt = self.optimal_lags
        sr = self.signal_pair.sampling_rate
        axes[1, 0].axvline(
            x=opt["best_kuramoto_lag"] / sr,
            color="b",
            linestyle="--",
            alpha=0.7,
            label=f'Best Kuramoto ({opt["best_kuramoto_lag"]/sr:.3f}s)',
        )
        axes[1, 0].axvline(
            x=opt["best_jrp_lag"] / sr,
            color="r",
            linestyle="--",
            alpha=0.7,
            label=f'Best JRP ({opt["best_jrp_lag"]/sr:.3f}s)',
        )
        axes[1, 0].axvline(
            x=opt["best_combined_lag"] / sr,
            color="k",
            linestyle="--",
            alpha=0.7,
            label=f'Best Combined ({opt["best_combined_lag"]/sr:.3f}s)',
        )
        axes[1, 0].legend()

        # Summary table
        axes[1, 1].axis("off")
        summary_text = (
            f"Optimal Lags:\n"
            f"  Kuramoto: {opt['best_kuramoto_lag']} steps ({opt['best_kuramoto_lag']/sr:.3f}s)\n"
            f"  JRP:      {opt['best_jrp_lag']} steps ({opt['best_jrp_lag']/sr:.3f}s)\n"
            f"  Combined: {opt['best_combined_lag']} steps ({opt['best_combined_lag']/sr:.3f}s)\n\n"
            f"Lag range: ±{self.max_lag} steps (±{self.max_lag/sr:.1f}s)\n"
            f"Lag step:  {self.lag_step} step(s) ({self.lag_step/sr:.3f}s)"
        )
        axes[1, 1].text(
            0.1, 0.5, summary_text, fontsize=12, verticalalignment="center", family="monospace"
        )

        plt.tight_layout()
        return fig

    def export_results(self, output_dir: str = "results_delay"):
        """Export delay characterization results."""
        Path(output_dir).mkdir(parents=True, exist_ok=True)

        # Combined results
        self.get_results().to_parquet(f"{output_dir}/lag_sweep_results.parquet")

        # Kuramoto results
        if self.kuramoto_results is not None:
            self.kuramoto_results.to_parquet(f"{output_dir}/kuramoto_lag_sweep.parquet")

        # JRP results
        if self.jrp_results is not None:
            self.jrp_results.to_parquet(f"{output_dir}/jrp_lag_sweep.parquet")

        # Save plots
        for name, plot_func in [
            ("kuramoto", self.plot_kuramoto),
            ("jrp", self.plot_jrp),
            ("combined", self.plot_combined),
        ]:
            fig = plot_func()
            if fig is not None:
                fig.savefig(f"{output_dir}/{name}_scores.png", dpi=300, bbox_inches="tight")
                plt.close(fig)

        # Summary text
        opt = self.get_optimal_lags()
        sr = self.signal_pair.sampling_rate
        with open(f"{output_dir}/delay_summary.txt", "w") as f:
            f.write(f"Delay Characterization Summary\n")
            f.write(f"==============================\n\n")
            f.write(f"Data source: {self.data_source.get_description()}\n")
            f.write(f"Sampling rate: {sr} Hz\n")
            f.write(f"Signal A: {self.signal_pair.name_a}\n")
            f.write(f"Signal B: {self.signal_pair.name_b}\n")
            f.write(f"Samples: {self.signal_pair.n_samples}\n")
            f.write(f"Lag range: ±{self.max_lag} steps (lag step: {self.lag_step})\n\n")
            f.write(f"Optimal Lags:\n")
            f.write(
                f"  Kuramoto: {opt['best_kuramoto_lag']} steps ({opt['best_kuramoto_lag']/sr:.3f}s)\n"
            )
            f.write(f"  JRP:      {opt['best_jrp_lag']} steps ({opt['best_jrp_lag']/sr:.3f}s)\n")
            f.write(
                f"  Combined: {opt['best_combined_lag']} steps ({opt['best_combined_lag']/sr:.3f}s)\n\n"
            )

            # Use combined results for scores
            if self.combined_results is not None:
                # Kuramoto at best lag
                best_k = self.combined_results.loc[
                    self.combined_results["lag"] == opt["best_kuramoto_lag"]
                ]
                if len(best_k) > 0:
                    best_k = best_k.iloc[0]
                    f.write(f"Kuramoto at best lag:\n")
                    f.write(f"  r_mean: {best_k['r_mean']:.4f}\n")
                    f.write(f"  frac_above_07: {best_k['frac_above_07']:.4f}\n")
                    f.write(f"  max_sustained_sec: {best_k['max_sustained_sec']:.3f}s\n")
                    f.write(f"  kuramoto_score: {best_k['kuramoto_score']:.4f}\n\n")

                # JRP at best lag
                jrp_valid = self.combined_results[
                    (self.combined_results["lag"] != -self.max_lag)
                    & (self.combined_results["lag"] != self.max_lag)
                    & (self.combined_results["jrp_RR"] > 0)
                ]
                if len(jrp_valid) > 0:
                    best_j = jrp_valid.loc[jrp_valid["jrp_score"].idxmax()]
                    f.write(f"JRP at best lag:\n")
                    f.write(f"  RR: {best_j['jrp_RR']:.4f}\n")
                    f.write(f"  DET: {best_j['jrp_DET']:.4f}\n")
                    f.write(f"  LAM: {best_j['jrp_LAM']:.4f}\n")
                    f.write(f"  jrp_score: {best_j['jrp_score']:.4f}\n\n")

        print(f"Results exported to {output_dir}/")
        return self
