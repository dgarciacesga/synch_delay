#!/usr/bin/env python3
"""Generate 6-panel workflow figures (a-f) with consistent styling."""

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from scipy.signal import hilbert
from scipy.spatial.distance import pdist, squareform
import sys
sys.path.insert(0, '/Users/david/Documents/CESGA/synch_delay/src')
from synch_analysis import LorenzDataSource, BelousovZhabotinskyDataSource, ParquetDataSource

# ─── Publication-quality style ───
plt.rcParams.update({
    'figure.figsize': (14, 8),
    'font.size': 11,
    'font.family': 'sans-serif',
    'font.sans-serif': ['Arial', 'DejaVu Sans', 'Liberation Sans'],
    'figure.dpi': 300,
    'savefig.dpi': 300,
    'savefig.bbox': 'tight',
    'savefig.pad_inches': 0.1,
    'figure.facecolor': 'white',
    'axes.facecolor': 'white',
    'axes.edgecolor': 'black',
    'axes.grid': False,
    'axes.axisbelow': True,
    'axes.spines.top': True,
    'axes.spines.right': True,
    'axes.linewidth': 0.8,
    'xtick.major.size': 4,
    'xtick.major.width': 0.8,
    'ytick.major.size': 4,
    'ytick.major.width': 0.8,
    'legend.frameon': True,
    'legend.framealpha': 0.9,
    'legend.edgecolor': 'black',
    'lines.linewidth': 1.0,
    'lines.markersize': 4,
    'image.cmap': 'binary',
    'image.origin': 'lower',
    'image.aspect': 'equal',
    'image.interpolation': 'nearest',
})

# ─── Helper functions (matching notebooks exactly) ───
def get_phase(signal):
    analytic = hilbert(signal)
    return np.angle(analytic)

def kuramoto_order_param(phi1, phi2):
    z = 0.5 * (np.exp(1j * phi1) + np.exp(1j * phi2))
    return np.abs(z)

def embed_time_series(x, m=3, tau=1):
    n = len(x)
    if n < (m - 1) * tau + 1:
        return np.array([])
    embedded = np.zeros((n - (m - 1) * tau, m))
    for i in range(m):
        embedded[:, i] = x[i * tau:n - (m - 1 - i) * tau]
    return embedded

def recurrence_plot(x, threshold=None, rate=0.05):
    n = len(x)
    if x.ndim == 1:
        x = x.reshape(-1, 1)
    dists = squareform(pdist(x, metric='euclidean'))
    if threshold is None:
        flat_dists = dists[np.triu_indices(n, k=1)]
        threshold = np.percentile(flat_dists, rate * 100)
    rp = dists <= threshold
    return rp, threshold

def joint_recurrence_plot(rp1, rp2):
    return rp1 & rp2

def jrp_rqa_metrics(jrp):
    n = jrp.shape[0]
    rr = np.sum(jrp) / (n * n)
    diag_lengths = []
    vert_lengths = []
    for offset in range(-n + 1, n):
        diag = np.diag(jrp, k=offset)
        if len(diag) < 2:
            continue
        in_line = False
        length = 0
        for val in diag:
            if val:
                if not in_line:
                    in_line = True
                    length = 1
                else:
                    length += 1
            else:
                if in_line and length >= 2:
                    diag_lengths.append(length)
                in_line = False
                length = 0
        if in_line and length >= 2:
            diag_lengths.append(length)
    det = sum(diag_lengths) / np.sum(jrp) if np.sum(jrp) > 0 else 0
    max_diag = max(diag_lengths) if diag_lengths else 0
    mean_diag = np.mean(diag_lengths) if diag_lengths else 0
    for col in range(n):
        vert = jrp[:, col]
        in_line = False
        length = 0
        for val in vert:
            if val:
                if not in_line:
                    in_line = True
                    length = 1
                else:
                    length += 1
            else:
                if in_line and length >= 2:
                    vert_lengths.append(length)
                in_line = False
                length = 0
        if in_line and length >= 2:
            vert_lengths.append(length)
    lam = sum(vert_lengths) / np.sum(jrp) if np.sum(jrp) > 0 else 0
    max_vert = max(vert_lengths) if vert_lengths else 0
    return {'RR': rr, 'DET': det, 'LAM': lam, 'max_diag': max_diag, 'mean_diag': mean_diag, 'max_vert': max_vert}

def shift_signal(signal, lag):
    if lag > 0:
        shifted = np.concatenate([np.full(lag, np.nan), signal[:-lag]])
    elif lag < 0:
        shifted = np.concatenate([signal[-lag:], np.full(-lag, np.nan)])
    else:
        shifted = signal.copy()
    return pd.Series(shifted).interpolate(limit_direction='both').values

def normalize_zero_centered(x):
    """Normalize to [-1, 1] centered at 0 (matching notebook)."""
    x = np.asarray(x, dtype=float)
    x_centered = x - np.mean(x)
    max_abs = np.max(np.abs(x_centered))
    if max_abs > 0:
        return x_centered / max_abs
    return x_centered

def smooth_signal(x, window=5):
    """Apply moving average smoothing (matching notebook)."""
    from scipy.ndimage import uniform_filter1d
    return uniform_filter1d(x, size=window, mode='reflect')

# ─── Workflow figure generator ───
def generate_workflow_figure(signal_a, signal_b, name_a, name_b, sampling_rate, lag, title_suffix, output_path,
                              normalize_func=normalize_zero_centered, smooth_window=5, rp_rate=0.05,
                              max_time_units=None, rp_max_time_units=None, kuramoto_smooth_window=1,
                              order_param_smooth_window=1, time_axis=None, trim_edges=0):
    """Generate 6-panel workflow figure with colormapped phase state space.
    
    Args:
        smooth_window: smoothing window for RP analysis
        kuramoto_smooth_window: smoothing window for Kuramoto/phase analysis (1=no smoothing)
        order_param_smooth_window: smoothing window for Kuramoto order parameter R(t) (1=no smoothing)
        time_axis: optional array of time values (e.g., actual timestamps)
        trim_edges: number of samples to discard from start and end to avoid edge effects
        max_time_units: max time units for time series panels (a, b, c)
        rp_max_time_units: max time units for RP/JRP panels (d, e, f); if None, uses max_time_units
    """
    # Apply lag to signal_b
    s1 = signal_a
    s2 = shift_signal(signal_b, lag)
    
    # Normalize (zero-centered to [-1, 1] matching notebook)
    s1_norm = normalize_func(s1)
    s2_norm = normalize_func(s2)
    
    # Smooth signals for Kuramoto/phase analysis (matching notebook)
    s1_kuramoto = smooth_signal(s1_norm, window=kuramoto_smooth_window)
    s2_kuramoto = smooth_signal(s2_norm, window=kuramoto_smooth_window)
    
    # Smooth signals for RP analysis (matching notebook)
    s1_smooth = smooth_signal(s1_norm, window=smooth_window)
    s2_smooth = smooth_signal(s2_norm, window=smooth_window)
    
    # Limit time series length if requested (for clarity)
    if max_time_units is not None:
        n_samples = int(max_time_units * sampling_rate)
        if n_samples < len(s1_norm):
            s1_norm = s1_norm[:n_samples]
            s2_norm = s2_norm[:n_samples]
        if n_samples < len(s1_kuramoto):
            s1_kuramoto = s1_kuramoto[:n_samples]
            s2_kuramoto = s2_kuramoto[:n_samples]
        if n_samples < len(s1_smooth):
            s1_smooth = s1_smooth[:n_samples]
            s2_smooth = s2_smooth[:n_samples]
        if time_axis is not None:
            time_axis = time_axis[:n_samples]
    
    # Additional limit for RP/JRP panels (panels d, e, f)
    if rp_max_time_units is not None:
        rp_n_samples = int(rp_max_time_units * sampling_rate)
        if rp_n_samples < len(s1_smooth):
            s1_smooth = s1_smooth[:rp_n_samples]
            s2_smooth = s2_smooth[:rp_n_samples]
    
    # Time axis (for panels a, b, c) - use full max_time_units length
    if time_axis is not None:
        time = time_axis
    else:
        time = np.arange(len(s1_norm)) / sampling_rate
    
    # Phases (use Kuramoto-smoothed signals)
    phi1 = get_phase(s1_kuramoto)
    phi2 = get_phase(s2_kuramoto)
    r = kuramoto_order_param(phi1, phi2)
    
    # Smoothed order parameter
    if order_param_smooth_window > 1:
        r_smooth = smooth_signal(r, window=order_param_smooth_window)
    else:
        r_smooth = None
    
    # Recurrence plots - use rp_max_time_units truncated signals
    m, tau, rate = 3, 1, rp_rate
    s1_emb = embed_time_series(s1_smooth, m=m, tau=tau)
    s2_emb = embed_time_series(s2_smooth, m=m, tau=tau)
    min_len = min(len(s1_emb), len(s2_emb))
    s1_emb = s1_emb[:min_len]
    s2_emb = s2_emb[:min_len]
    
    rp1, _ = recurrence_plot(s1_emb, rate=rate)
    rp2, _ = recurrence_plot(s2_emb, rate=rate)
    jrp = joint_recurrence_plot(rp1, rp2)
    metrics = jrp_rqa_metrics(jrp)
    
    # Trim edges to avoid boundary effects
    if trim_edges > 0:
        trim = trim_edges
        if trim < len(s1_norm):
            s1_norm = s1_norm[trim:-trim]
            s2_norm = s2_norm[trim:-trim]
            s1_kuramoto = s1_kuramoto[trim:-trim]
            s2_kuramoto = s2_kuramoto[trim:-trim]
            s1_smooth = s1_smooth[trim:-trim]
            s2_smooth = s2_smooth[trim:-trim]
            phi1 = phi1[trim:-trim]
            phi2 = phi2[trim:-trim]
            r = r[trim:-trim]
            if r_smooth is not None:
                r_smooth = r_smooth[trim:-trim]
            time = time[trim:-trim]
    
    # ─── Create 6-panel figure ───
    fig = plt.figure(figsize=(14, 8))
    gs = fig.add_gridspec(2, 3, hspace=0.35, wspace=0.3)
    
    # (a) Time series - show un-smoothed signals to make lag misalignment visible
    ax1 = fig.add_subplot(gs[0, 0])
    ax1.plot(time, s1_norm, label=name_a, alpha=0.8, linewidth=0.8)
    ax1.plot(time, s2_norm, label=name_b, alpha=0.8, linewidth=0.8)
    ax1.set_xlabel('Time')
    ax1.set_ylabel('Normalized amplitude')
    ax1.set_title('(a) Time series')
    ax1.legend(frameon=True, framealpha=0.9, edgecolor='black', fontsize=9)
    
    # (b) Phase state space - scatter colored by R(t) using viridis colormap
    ax2 = fig.add_subplot(gs[0, 1])
    sc = ax2.scatter(phi1, phi2, c=r, cmap='viridis', alpha=0.5, s=2, vmin=0, vmax=1)
    ax2.plot([-np.pi, np.pi], [-np.pi, np.pi], 'k--', alpha=0.5, linewidth=0.8, label='Diagonal')
    cbar = fig.colorbar(sc, ax=ax2, shrink=0.8, pad=0.02)
    cbar.set_label('Kuramoto R(t)')
    ax2.set_xlabel(f'Phase {name_a} (rad)')
    ax2.set_ylabel(f'Phase {name_b} (rad)')
    ax2.set_title('(b) Phase state space')
    ax2.set_xlim(-np.pi, np.pi)
    ax2.set_ylim(-np.pi, np.pi)
    ax2.legend(frameon=True, framealpha=0.9, edgecolor='black', fontsize=9)
    
    # (c) Kuramoto order parameter
    ax3 = fig.add_subplot(gs[0, 2])
    ax3.plot(time, r, 'b-', linewidth=0.8, alpha=0.3, label='R(t) raw')
    if r_smooth is not None:
        ax3.plot(time, r_smooth, 'b-', linewidth=1.2, alpha=0.9, label=f'R(t) smoothed (w={order_param_smooth_window})')
    ax3.axhline(y=0.7, color='g', linestyle='--', alpha=0.6, label='Sync threshold (0.7)')
    ax3.set_xlabel('Time')
    ax3.set_ylabel('R(t)')
    ax3.set_title('(c) Kuramoto order parameter')
    ax3.set_ylim(0, 1.05)
    ax3.legend(frameon=True, framealpha=0.9, edgecolor='black', fontsize=9)
    
    # (d) RP of signal A
    ax4 = fig.add_subplot(gs[1, 0])
    im4 = ax4.imshow(rp1.T, origin='lower', cmap='binary', aspect='equal', interpolation='nearest')
    ax4.set_xlabel('Time')
    ax4.set_ylabel('Time')
    ax4.set_title(f'(d) Recurrence plot: {name_a}\nRR={metrics["RR"]:.3f}, DET={metrics["DET"]:.3f}')
    
    # (e) RP of signal B
    ax5 = fig.add_subplot(gs[1, 1])
    im5 = ax5.imshow(rp2.T, origin='lower', cmap='binary', aspect='equal', interpolation='nearest')
    ax5.set_xlabel('Time')
    ax5.set_ylabel('Time')
    ax5.set_title(f'(e) Recurrence plot: {name_b}\nRR={metrics["RR"]:.3f}, DET={metrics["DET"]:.3f}')
    
    # (f) Joint RP
    ax6 = fig.add_subplot(gs[1, 2])
    im6 = ax6.imshow(jrp.T, origin='lower', cmap='binary', aspect='equal', interpolation='nearest')
    ax6.set_xlabel('Time')
    ax6.set_ylabel('Time')
    ax6.set_title(f'(f) Joint recurrence plot\nRR={metrics["RR"]:.3f}, DET={metrics["DET"]:.3f}, LAM={metrics["LAM"]:.3f}')
    
    fig.suptitle(title_suffix, fontsize=13, y=0.98)
    fig.savefig(output_path, dpi=300, bbox_inches='tight', pad_inches=0.1, facecolor='white')
    plt.close(fig)
    print(f'Saved: {output_path}')

# ─── Load data and generate figures ───
print("Generating workflow figures...")

# Lorenz (matching notebook: iterations=7000, delay_steps=150, noise_std=0.05)
print("\n--- LORENZ ---")
lorenz = LorenzDataSource(a=10.0, b=28.0, c=8.0/3.0, dt=0.01, initial_values=[0.01, 0, 0.3],
                           iterations=7000, variable='x', delay_steps=150, noise_std=0.05, sampling_rate=100.0)
s = lorenz.load()
sig_a = s.signal_a
sig_b = s.signal_b

# Lorenz uses rate=0.05, smooth_window=1, fewer time units for RP clarity
generate_workflow_figure(sig_a, sig_b, 'Source', 'Delayed', 100.0, 0,
    'Lorenz system: before delay compensation (true delay = 1.50 s)',
    '/Users/david/Documents/CESGA/synch_paper/figures/intro_conceptual.png',
    smooth_window=1, rp_rate=0.05, max_time_units=15)

generate_workflow_figure(sig_a, sig_b, 'Source', 'Delayed', 100.0, -150,
    'Lorenz system: after delay compensation (aligned at τ = 1.50 s)',
    '/Users/david/Documents/CESGA/synch_paper/figures/intro_aligned.png',
    smooth_window=1, rp_rate=0.05, max_time_units=15)

# BZ (matching notebook: iterations=3000, delay_steps=30, noise_std=0.005, transient=1500)
print("\n--- BELUSOV-ZHABOTINSKY ---")
bz = BelousovZhabotinskyDataSource(f=1.0, q=0.05, eps=0.02, dt=0.01,
                                    initial_values=[0.1, 0.1], iterations=3000,
                                    variable='x', delay_steps=30, noise_std=0.005,
                                    sampling_rate=100.0, transient=1500)
s = bz.load()
sig_a = s.signal_a
sig_b = s.signal_b

# BZ uses rate=0.1, smooth_window=1, more time for time series, fewer for RP/JRP
generate_workflow_figure(sig_a, sig_b, 'Source', 'Delayed', 100.0, 0,
    'Belousov–Zhabotinsky (Oregonator): before delay compensation (true delay = 0.30 s)',
    '/Users/david/Documents/CESGA/synch_paper/figures/bz_workflow_before.png',
    smooth_window=1, rp_rate=0.1, max_time_units=20, rp_max_time_units=10, trim_edges=300)

generate_workflow_figure(sig_a, sig_b, 'Source', 'Delayed', 100.0, -30,
    'Belousov–Zhabotinsky (Oregonator): after delay compensation (aligned at τ = 0.30 s)',
    '/Users/david/Documents/CESGA/synch_paper/figures/bz_workflow_after.png',
    smooth_window=1, rp_rate=0.1, max_time_units=20, rp_max_time_units=10, trim_edges=300)

# Industrial (T11/T12) - matching notebook exactly
print("\n--- INDUSTRIAL ---")
from scipy.ndimage import uniform_filter1d

# Load data as in notebook
df = pd.read_parquet('/Users/david/Documents/CESGA/synch_delay/data/datos_ind.pqt')
df['fecha'] = pd.to_datetime(df['fecha'])
df = df.set_index('fecha')

start_time = '2021-11-03 12:10:00'
end_time = '2021-11-03 12:30:00'
df_hour = df.loc[start_time:end_time].copy()
print(f"Window: {df_hour.index[0]} to {df_hour.index[-1]}")
print(f"Length: {len(df_hour)} samples")

# Extract signals: sensor A (upstream) as source, sensor B (downstream) as delayed
sig_a = df_hour['VarB'].values  # sensor A
sig_b = df_hour['VarA'].values  # sensor B

# Normalize (matching notebook)
def normalize_zero_centered(x):
    x = np.asarray(x, dtype=float)
    x_centered = x - np.mean(x)
    max_abs = np.max(np.abs(x_centered))
    if max_abs > 0:
        return x_centered / max_abs
    return x_centered

sig_a_norm = normalize_zero_centered(sig_a)
sig_b_norm = normalize_zero_centered(sig_b)

# Real lag calculation
real_lag = int(18600 / df_hour['Velocidad'].mean())
print(f"Real lag (distance/speed): {real_lag}s ({real_lag/60:.1f} min)")

# Time axis using actual timestamps
time_axis = df_hour.index.values

# Pass raw (normalized, unsmoothed) signals; function will smooth internally
# For Figure 6 (before): NO shift applied - show raw signals as-is with lag=0
generate_workflow_figure(sig_a_norm, sig_b_norm, 'Sensor A', 'Sensor B', 1.0, 0,
        'Industrial measurements: raw signals (no alignment applied)',
        '/Users/david/Documents/CESGA/synch_paper/figures/industrial_workflow_before.png',
        smooth_window=5, rp_rate=0.1, order_param_smooth_window=20, time_axis=time_axis, trim_edges=60)

generate_workflow_figure(sig_a_norm, sig_b_norm, 'Sensor A', 'Sensor B', 1.0, 90,
        'Industrial measurements: after alignment at detected 90 s lag',
        '/Users/david/Documents/CESGA/synch_paper/figures/industrial_workflow_after.png',
        smooth_window=5, rp_rate=0.1, order_param_smooth_window=20, time_axis=time_axis, trim_edges=60)

print("\nAll workflow figures generated!")