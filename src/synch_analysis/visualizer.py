"""Visualization tools for synchronization analysis."""

from typing import Tuple, Optional, List
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.animation import FuncAnimation

from .analyzer import SynchronizationAnalyzer
from .core import SignalPair


class SynchronizationVisualizer:
    """Visualization tools for synchronization analysis."""

    def __init__(self, analyzer: SynchronizationAnalyzer, figsize: Tuple[int, int] = (15, 10)):
        self.analyzer = analyzer
        self.figsize = figsize

    def plot_signals(self, ax=None, n_samples: Optional[int] = None):
        """Plot raw signals."""
        if ax is None:
            fig, ax = plt.subplots(figsize=self.figsize)

        sig_a = self.analyzer.signal_pair.signal_a
        sig_b = self.analyzer.signal_pair.signal_b

        if n_samples:
            sig_a = sig_a[:n_samples]
            sig_b = sig_b[:n_samples]

        time = np.arange(len(sig_a)) / self.analyzer.signal_pair.sampling_rate

        ax.plot(time, sig_a, label=self.analyzer.signal_pair.name_a, alpha=0.7)
        ax.plot(time, sig_b, label=self.analyzer.signal_pair.name_b, alpha=0.7)
        ax.set_xlabel("Time")
        ax.set_ylabel("Amplitude")
        ax.set_title("Raw Signals")
        ax.legend()
        ax.grid(True, alpha=0.3)

        return ax

    def plot_hilbert_components(self, ax=None):
        """Plot Hilbert transform components (real vs imaginary)."""
        if ax is None:
            fig, axes = plt.subplots(1, 2, figsize=self.figsize)
        else:
            axes = ax if isinstance(ax, (list, np.ndarray)) else [ax]

        if self.analyzer.hilbert_a is None:
            self.analyzer.compute_hilbert_transform()

        for i, (hilbert, name) in enumerate([
            (self.analyzer.hilbert_a, self.analyzer.signal_pair.name_a),
            (self.analyzer.hilbert_b, self.analyzer.signal_pair.name_b),
        ]):
            ax = axes[i] if i < len(axes) else axes[0]
            ax.plot(hilbert.real, hilbert.imag, ",", alpha=0.5, markersize=1)
            ax.set_xlabel("Real")
            ax.set_ylabel("Imaginary")
            ax.set_title(f"Analytic Signal: {name}")
            ax.set_aspect("equal")
            ax.grid(True, alpha=0.3)

        return axes

    def plot_phases(self, ax=None):
        """Plot instantaneous phases."""
        if ax is None:
            fig, ax = plt.subplots(figsize=self.figsize)

        if self.analyzer.phase_a is None:
            self.analyzer.compute_hilbert_transform()

        time = np.arange(len(self.analyzer.phase_a)) / self.analyzer.signal_pair.sampling_rate

        ax.plot(time, self.analyzer.phase_a, label=self.analyzer.signal_pair.name_a, alpha=0.7)
        ax.plot(time, self.analyzer.phase_b, label=self.analyzer.signal_pair.name_b, alpha=0.7)
        ax.set_xlabel("Time")
        ax.set_ylabel("Phase (rad)")
        ax.set_title("Instantaneous Phases")
        ax.legend()
        ax.grid(True, alpha=0.3)

        return ax

    def plot_phase_portrait(self, ax=None):
        """Plot phases on unit circle."""
        if ax is None:
            fig, ax = plt.subplots(figsize=(8, 8))

        if self.analyzer.phase_a is None:
            self.analyzer.compute_hilbert_transform()

        # Unit circle
        theta = np.linspace(0, 2 * np.pi, 200)
        ax.plot(np.cos(theta), np.sin(theta), "k-", alpha=0.3, linewidth=1)

        # Phase points
        ax.plot(
            np.cos(self.analyzer.phase_a),
            np.sin(self.analyzer.phase_a),
            "o",
            label=self.analyzer.signal_pair.name_a,
            alpha=0.6,
            markersize=3,
        )
        ax.plot(
            np.cos(self.analyzer.phase_b),
            np.sin(self.analyzer.phase_b),
            "*",
            label=self.analyzer.signal_pair.name_b,
            alpha=0.6,
            markersize=5,
        )

        ax.set_aspect("equal")
        ax.set_xlabel("cos(φ)")
        ax.set_ylabel("sin(φ)")
        ax.set_title("Phase Portrait on Unit Circle")
        ax.legend()
        ax.grid(True, alpha=0.3)
        ax.set_xlim(-1.2, 1.2)
        ax.set_ylim(-1.2, 1.2)

        return ax

    def plot_order_parameter(self, ax=None, sliding_window: Optional[int] = None):
        """Plot Kuramoto order parameter over time."""
        if ax is None:
            fig, ax = plt.subplots(figsize=self.figsize)

        if self.analyzer.order_parameter is None:
            self.analyzer.compute_order_parameter()

        time = np.arange(len(self.analyzer.order_parameter)) / self.analyzer.signal_pair.sampling_rate

        ax.plot(time, self.analyzer.order_parameter, "b-", alpha=0.5, label="R(t)")

        if sliding_window:
            sliding = self.analyzer.compute_sliding_order_parameter(sliding_window)
            ax.plot(time, sliding, "r-", linewidth=2, label=f"Sliding (w={sliding_window})")

        ax.axhline(y=0.8, color="g", linestyle="--", alpha=0.5, label="Sync threshold (0.8)")
        ax.set_xlabel("Time")
        ax.set_ylabel("Order Parameter R(t)")
        ax.set_title("Kuramoto Order Parameter")
        ax.set_ylim(0, 1.05)
        ax.legend()
        ax.grid(True, alpha=0.3)

        return ax

    def plot_phase_difference(self, ax=None):
        """Plot phase difference over time."""
        if ax is None:
            fig, ax = plt.subplots(figsize=self.figsize)

        if self.analyzer.phase_diff is None:
            self.analyzer.compute_order_parameter()

        time = np.arange(len(self.analyzer.phase_diff)) / self.analyzer.signal_pair.sampling_rate

        ax.plot(time, self.analyzer.phase_diff, "g-", alpha=0.7)
        ax.axhline(y=0, color="k", linestyle="-", alpha=0.3)
        ax.axhline(y=np.pi, color="r", linestyle="--", alpha=0.5, label="π")
        ax.axhline(y=-np.pi, color="r", linestyle="--", alpha=0.5, label="-π")
        ax.set_xlabel("Time")
        ax.set_ylabel("Phase Difference (rad)")
        ax.set_title("Phase Difference φ₁ - φ₂")
        ax.legend()
        ax.grid(True, alpha=0.3)

        return ax

    def create_dashboard(self, sliding_window: int = 50, n_signal_samples: int = 500):
        """Create a comprehensive dashboard."""
        fig = plt.figure(figsize=(20, 16))

        # Grid layout
        gs = fig.add_gridspec(3, 3, hspace=0.3, wspace=0.3)

        # Raw signals
        ax1 = fig.add_subplot(gs[0, 0])
        self.plot_signals(ax1, n_samples=n_signal_samples)

        # Hilbert components
        ax2 = fig.add_subplot(gs[0, 1])
        ax3 = fig.add_subplot(gs[0, 2])
        self.plot_hilbert_components([ax2, ax3])

        # Phases
        ax4 = fig.add_subplot(gs[1, 0])
        self.plot_phases(ax4)

        # Phase portrait
        ax5 = fig.add_subplot(gs[1, 1])
        self.plot_phase_portrait(ax5)

        # Order parameter
        ax6 = fig.add_subplot(gs[1, 2])
        self.plot_order_parameter(ax6, sliding_window=sliding_window)

        # Phase difference
        ax7 = fig.add_subplot(gs[2, 0])
        self.plot_phase_difference(ax7)

        # Summary stats
        ax8 = fig.add_subplot(gs[2, 1:])
        ax8.axis("off")
        stats = self.analyzer.get_summary_stats()
        stats_text = "\n".join([f"{k}: {v:.4f}" for k, v in stats.items()])
        ax8.text(
            0.1, 0.9, stats_text, transform=ax8.transAxes, fontsize=12,
            verticalalignment="top", fontfamily="monospace",
            bbox=dict(boxstyle="round", facecolor="wheat", alpha=0.5)
        )
        ax8.set_title("Summary Statistics")

        # Main title
        fig.suptitle(
            f"Synchronization Analysis: {self.analyzer.signal_pair.name_a} vs {self.analyzer.signal_pair.name_b}",
            fontsize=16, y=0.98
        )

        return fig

    def animate_phases(self, interval: int = 50, trail_length: int = 50):
        """Create animation of phases on unit circle."""
        if self.analyzer.phase_a is None:
            self.analyzer.compute_hilbert_transform()

        fig, ax = plt.subplots(figsize=(8, 8))

        theta = np.linspace(0, 2 * np.pi, 200)
        ax.plot(np.cos(theta), np.sin(theta), "k-", alpha=0.3)
        ax.set_aspect("equal")
        ax.set_xlim(-1.2, 1.2)
        ax.set_ylim(-1.2, 1.2)
        ax.set_xlabel("cos(φ)")
        ax.set_ylabel("sin(φ)")
        ax.set_title("Phase Evolution Animation")

        # Initialize points
        point_a, = ax.plot([], [], "ro", markersize=10, label=self.analyzer.signal_pair.name_a)
        point_b, = ax.plot([], [], "bs", markersize=10, label=self.analyzer.signal_pair.name_b)
        trail_a, = ax.plot([], [], "r-", alpha=0.3, linewidth=1)
        trail_b, = ax.plot([], [], "b-", alpha=0.3, linewidth=1)

        ax.legend()

        def init():
            point_a.set_data([], [])
            point_b.set_data([], [])
            trail_a.set_data([], [])
            trail_b.set_data([], [])
            return point_a, point_b, trail_a, trail_b

        def animate(frame):
            point_a.set_data([np.cos(self.analyzer.phase_a[frame])], [np.sin(self.analyzer.phase_a[frame])])
            point_b.set_data([np.cos(self.analyzer.phase_b[frame])], [np.sin(self.analyzer.phase_b[frame])])

            start = max(0, frame - trail_length)
            trail_a.set_data(
                np.cos(self.analyzer.phase_a[start:frame]),
                np.sin(self.analyzer.phase_a[start:frame])
            )
            trail_b.set_data(
                np.cos(self.analyzer.phase_b[start:frame]),
                np.sin(self.analyzer.phase_b[start:frame])
            )

            return point_a, point_b, trail_a, trail_b

        anim = FuncAnimation(fig, animate, frames=len(self.analyzer.phase_a),
                           init_func=init, interval=interval, blit=True)

        plt.close()
        return anim