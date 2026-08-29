"""Joint Recurrence Plot (JRP) analysis functions."""

from typing import Dict, Tuple, Optional, List
import numpy as np
import pandas as pd
from scipy.spatial.distance import pdist, squareform
from scipy.ndimage import uniform_filter1d


def embed_time_series(x: np.ndarray, m: int = 3, tau: int = 1) -> np.ndarray:
    """Time-delay embedding."""
    n = len(x)
    if n < (m - 1) * tau + 1:
        return np.array([])
    embedded = np.zeros((n - (m - 1) * tau, m))
    for i in range(m):
        embedded[:, i] = x[i * tau : n - (m - 1 - i) * tau]
    return embedded


def recurrence_plot(
    x: np.ndarray, threshold: Optional[float] = None, rate: float = 0.05
) -> Tuple[np.ndarray, float]:
    """Compute recurrence plot for a single time series."""
    n = len(x)
    if x.ndim == 1:
        x = x.reshape(-1, 1)
    dists = squareform(pdist(x, metric="euclidean"))

    if threshold is None:
        # Use fixed recurrence rate
        dist_flat = dists[np.triu_indices(n, k=1)]
        threshold = np.percentile(dist_flat, rate * 100)

    rp = (dists <= threshold).astype(int)
    return rp, threshold


def joint_recurrence_plot(rp1: np.ndarray, rp2: np.ndarray) -> np.ndarray:
    """Compute joint recurrence plot from two individual RPs."""
    return rp1 * rp2


def jrp_rqa_metrics(jrp: np.ndarray, min_diag: int = 2, min_vert: int = 2) -> Dict[str, float]:
    """Compute Recurrence Quantification Analysis metrics from JRP."""
    n = jrp.shape[0]
    if n == 0:
        return {"RR": 0.0, "DET": 0.0, "LAM": 0.0, "max_diag": 0, "mean_diag": 0.0, "max_vert": 0}

    # Recurrence Rate
    RR = np.sum(jrp) / (n * n)

    # Diagonal lines (determinism)
    diag_lengths = []
    for k in range(-n + 1, n):
        diag = np.diag(jrp, k=k)
        length = 0
        for val in diag:
            if val == 1:
                length += 1
            elif length >= min_diag:
                diag_lengths.append(length)
                length = 0
            else:
                length = 0
        if length >= min_diag:
            diag_lengths.append(length)

    diag_lengths = np.array(diag_lengths)
    total_diag_points = np.sum(diag_lengths) if len(diag_lengths) > 0 else 0
    total_recur_points = np.sum(jrp)

    DET = total_diag_points / total_recur_points if total_recur_points > 0 else 0.0
    max_diag = np.max(diag_lengths) if len(diag_lengths) > 0 else 0
    mean_diag = np.mean(diag_lengths) if len(diag_lengths) > 0 else 0.0

    # Vertical lines (laminarity)
    vert_lengths = []
    for j in range(n):
        length = 0
        for i in range(n):
            if jrp[i, j] == 1:
                length += 1
            elif length >= min_vert:
                vert_lengths.append(length)
                length = 0
            else:
                length = 0
        if length >= min_vert:
            vert_lengths.append(length)

    vert_lengths = np.array(vert_lengths)
    total_vert_points = np.sum(vert_lengths) if len(vert_lengths) > 0 else 0
    LAM = total_vert_points / total_recur_points if total_recur_points > 0 else 0.0
    max_vert = np.max(vert_lengths) if len(vert_lengths) > 0 else 0

    return {
        "RR": float(RR),
        "DET": float(DET),
        "LAM": float(LAM),
        "max_diag": int(max_diag),
        "mean_diag": float(mean_diag),
        "max_vert": int(max_vert),
    }


def compute_jrp_metrics(
    signal_a: np.ndarray,
    signal_b: np.ndarray,
    m: int = 3,
    tau: int = 1,
    rate: float = 0.05,
    min_diag: int = 2,
    min_vert: int = 2,
    smooth_size: int = 5,
) -> Dict[str, float]:
    """Compute full JRP metrics for a signal pair."""
    # Smooth signals
    s1_smooth = uniform_filter1d(signal_a, size=smooth_size, mode="reflect")
    s2_smooth = uniform_filter1d(signal_b, size=smooth_size, mode="reflect")

    # Embed
    s1_emb = embed_time_series(s1_smooth, m=m, tau=tau)
    s2_emb = embed_time_series(s2_smooth, m=m, tau=tau)

    min_len = min(len(s1_emb), len(s2_emb))
    if min_len < 50:
        return {"RR": 0.0, "DET": 0.0, "LAM": 0.0, "max_diag": 0, "mean_diag": 0.0, "max_vert": 0}

    s1_emb = s1_emb[:min_len]
    s2_emb = s2_emb[:min_len]

    # Individual RPs
    rp1, _ = recurrence_plot(s1_emb, rate=rate)
    rp2, _ = recurrence_plot(s2_emb, rate=rate)

    # Joint RP
    jrp = joint_recurrence_plot(rp1, rp2)

    return jrp_rqa_metrics(jrp, min_diag=min_diag, min_vert=min_vert)


def lag_sweep_jrp(
    signal_a: np.ndarray,
    signal_b: np.ndarray,
    lags: np.ndarray,
    m: int = 3,
    tau: int = 1,
    rate: float = 0.05,
    smooth_size: int = 5,
    sampling_rate: float = 1.0,
) -> pd.DataFrame:
    """Perform JRP lag sweep.

    Positive lag means signal A is delayed (shifted forward) relative to signal B.
    """
    results = []

    # Smooth signals once (signal_b doesn't shift)
    s1_smooth = uniform_filter1d(signal_a, size=smooth_size, mode="reflect")
    s2_smooth = uniform_filter1d(signal_b, size=smooth_size, mode="reflect")
    s2_emb = embed_time_series(s2_smooth, m=m, tau=tau)

    for lag in lags:
        # Shift signal_a (positive lag = delay signal A)
        if lag > 0:
            s1_shifted = np.concatenate([np.full(lag, np.nan), s1_smooth[:-lag]])
        elif lag < 0:
            s1_shifted = np.concatenate([s1_smooth[-lag:], np.full(-lag, np.nan)])
        else:
            s1_shifted = s1_smooth.copy()

        # Interpolate NaN
        s1_shifted = pd.Series(s1_shifted).interpolate(limit_direction="both").values

        # Embed shifted signal
        s1_emb = embed_time_series(s1_shifted, m=m, tau=tau)
        min_len = min(len(s1_emb), len(s2_emb))

        if min_len < 50:
            metrics = {
                "RR": 0.0,
                "DET": 0.0,
                "LAM": 0.0,
                "max_diag": 0,
                "mean_diag": 0.0,
                "max_vert": 0,
            }
        else:
            s1_emb = s1_emb[:min_len]
            s2_emb_trunc = s2_emb[:min_len]

            rp1, _ = recurrence_plot(s1_emb, rate=rate)
            rp2, _ = recurrence_plot(s2_emb_trunc, rate=rate)
            jrp = joint_recurrence_plot(rp1, rp2)
            metrics = jrp_rqa_metrics(jrp)

        results.append(
            {
                "lag": int(lag),
                "lag_sec": lag / sampling_rate,
                "jrp_RR": metrics["RR"],
                "jrp_DET": metrics["DET"],
                "jrp_LAM": metrics["LAM"],
                "jrp_max_diag": metrics["max_diag"],
                "jrp_mean_diag": metrics["mean_diag"],
                "jrp_max_vert": metrics["max_vert"],
            }
        )

    return pd.DataFrame(results)


def lag_sweep_kuramoto(
    signal_a: np.ndarray,
    signal_b: np.ndarray,
    lags: np.ndarray,
    sampling_rate: float = 100.0,
) -> pd.DataFrame:
    """Perform Kuramoto lag sweep.

    Positive lag means signal A is delayed (shifted forward) relative to signal B.
    """
    from scipy.signal import hilbert

    results = []

    for lag in lags:
        # Shift signal_a (positive lag = delay signal A)
        if lag > 0:
            s1_shifted = np.concatenate([np.full(lag, np.nan), signal_a[:-lag]])
        elif lag < 0:
            s1_shifted = np.concatenate([signal_a[-lag:], np.full(-lag, np.nan)])
        else:
            s1_shifted = signal_a.copy()

        # Interpolate NaN
        s1_shifted = pd.Series(s1_shifted).interpolate(limit_direction="both").values

        # Compute phases
        phi1 = np.angle(hilbert(s1_shifted))
        phi2 = np.angle(hilbert(signal_b))

        # Kuramoto order parameter
        z = 0.5 * (np.exp(1j * phi1) + np.exp(1j * phi2))
        R = np.abs(z)
        phase_diff = np.angle(np.exp(1j * phi1) / np.exp(1j * phi2))

        # Metrics
        r_mean = float(np.mean(R))
        frac_above_07 = float(np.mean(R > 0.7))
        max_sustained = 0
        current = 0
        for val in R:
            if val > 0.7:
                current += 1
            else:
                max_sustained = max(max_sustained, current)
                current = 0
        max_sustained = max(max_sustained, current)
        max_sustained_sec = max_sustained / sampling_rate

        results.append(
            {
                "lag": int(lag),
                "lag_sec": lag / sampling_rate,
                "r_mean": r_mean,
                "frac_above_07": frac_above_07,
                "max_sustained_sec": max_sustained_sec,
            }
        )

    return pd.DataFrame(results)


def compute_scores(
    kuramoto_df: pd.DataFrame,
    jrp_df: pd.DataFrame,
    max_lag: int,
) -> pd.DataFrame:
    """Compute combined scores from Kuramoto and JRP results."""
    # Both dataframes should have 'lag' and 'lag_sec' columns
    merged = (
        kuramoto_df.merge(jrp_df, on=["lag", "lag_sec"], how="outer").sort_values("lag").reset_index(drop=True)
    )

    def normalize(series: pd.Series) -> pd.Series:
        min_v, max_v = series.min(), series.max()
        if max_v > min_v:
            return (series - min_v) / (max_v - min_v)
        return pd.Series(0.0, index=series.index)

    # Kuramoto score: normalized(frac_above_07) * normalized(r_mean)
    merged["kuramoto_score"] = normalize(merged["frac_above_07"]) * normalize(merged["r_mean"])

    # JRP score: normalized RR only (excluding extreme lags)
    merged["jrp_score"] = 0.0
    jrp_valid = merged[
        (merged["lag"] != -max_lag) & (merged["lag"] != max_lag) & (merged["jrp_RR"] > 0)
    ].copy()

    if len(jrp_valid) > 0:
        jrp_scores = normalize(jrp_valid["jrp_RR"])
        merged.loc[jrp_valid.index, "jrp_score"] = jrp_scores

    # Combined score: arithmetic mean of normalized scores
    merged["combined_score"] = (merged["kuramoto_score"] + merged["jrp_score"]) / 2

    return merged


def find_optimal_lags(results_df: pd.DataFrame, max_lag: int) -> Dict[str, int]:
    """Find optimal lags from combined results."""
    best_kuramoto = int(results_df.loc[results_df["kuramoto_score"].idxmax(), "lag"])

    jrp_valid = results_df[
        (results_df["lag"] != -max_lag)
        & (results_df["lag"] != max_lag)
        & (results_df["jrp_RR"] > 0)
    ]
    best_jrp = (
        int(jrp_valid.loc[jrp_valid["jrp_score"].idxmax(), "lag"]) if len(jrp_valid) > 0 else 0
    )

    best_combined = int(results_df.loc[results_df["combined_score"].idxmax(), "lag"])

    return {
        "best_kuramoto_lag": best_kuramoto,
        "best_jrp_lag": best_jrp,
        "best_combined_lag": best_combined,
    }
