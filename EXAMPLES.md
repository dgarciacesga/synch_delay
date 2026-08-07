# Usage Examples

Complete usage examples for `synch_analysis`.

---

## Quick Start

```python
from synch_analysis import LorenzDataSource, SynchronizationPipeline

# Lorenz attractor with sensor delay simulation
lorenz = LorenzDataSource(
    a=10.0, b=28.0, c=8.0/3.0,
    initial_values=[0.01, 0, 0.3],
    iterations=5000,
    delay_steps=150,   # 1.5s delay at 100 Hz sampling
    noise_std=0.05,    # optional measurement noise
    sampling_rate=100.0
)

# Run analysis pipeline
pipeline = SynchronizationPipeline(lorenz).run()

# View dashboard
pipeline.plot_dashboard()

# Get statistics
stats = pipeline.get_stats()
print(f"Mean R: {stats['mean_R']:.4f}")
print(f"Sync ratio: {stats['sync_ratio']:.2%}")

# Export results
from synch_analysis import export_results
export_results(pipeline, "results/lorenz_analysis")
```

---

## Data Source Examples

### Lorenz Attractor

```python
from synch_analysis import LorenzDataSource, SynchronizationPipeline
import numpy as np

# Classic chaotic regime with sensor delay
lorenz = LorenzDataSource(
    a=10.0,
    b=28.0,
    c=8.0/3.0,
    dt=0.01,
    initial_values=[0.01, 0, 0.3],
    iterations=5000,
    variable="x",  # or "y", "z"
    delay_steps=150,    # Simulated sensor delay (steps)
    noise_std=0.05,     # Optional measurement noise
    sampling_rate=100.0
)

pipeline = SynchronizationPipeline(lorenz).run()
pipeline.plot_dashboard(sliding_window=100)
```

**Variants:**
```python
# Periodic regime (b < 24.74)
lorenz_periodic = LorenzDataSource(b=10.0, iterations=3000)

# Different variables
lorenz_y = LorenzDataSource(variable="y", iterations=2000)

# No delay - identical signals (backward compatible)
lorenz_copy = LorenzDataSource(
    initial_values=[0.01, 0, 0.3],
    iterations=3000,
    delay_steps=0  # Creates copy of signal_a as signal_b
)

# Delay detection: sweep delay to find true sensor delay
for delay in range(0, 300, 10):
    lorenz = LorenzDataSource(
        initial_values=[0.01, 0, 0.3],
        iterations=2000,
        delay_steps=delay,
        noise_std=0.02
    )
    pipeline = SynchronizationPipeline(lorenz).run()
    stats = pipeline.get_stats()
    print(f"Delay {delay:3d}: Mean R = {stats['mean_R']:.4f}")
```

---

### Sinusoidal Signals

```python
from synch_analysis import SinusoidDataSource, SynchronizationPipeline
import numpy as np

# Phase-locked with delay
sinusoid = SinusoidDataSource(
    ph0_a=0.0,
    ph0_b=np.pi/4,       # 45° phase shift
    frq_a=1.0,
    frq_b=1.0,           # Same frequency
    pers=10,             # 10 periods
    delay_a=0,
    delay_b=5,           # 5-sample delay
    iterations=2000,
    sampling_rate=100.0
)

pipeline = SynchronizationPipeline(sinusoid).run()
pipeline.plot_dashboard()
```

**Variants:**
```python
# Frequency mismatch (beat phenomenon)
sinusoid_beat = SinusoidDataSource(
    frq_a=1.0,
    frq_b=1.02,          # 2% frequency difference
    pers=20,
    iterations=5000
)

# Quadrature signals
sinusoid_quad = SinusoidDataSource(
    ph0_a=0.0,
    ph0_b=np.pi/2,       # 90° phase shift
    frq_a=1.0,
    frq_b=1.0,
    pers=5
)

# Different waveforms via frequency modulation
sinusoid_fm = SinusoidDataSource(
    frq_a=1.0,
    frq_b=1.5,           # 1.5x frequency
    pers=3
)
```

---

### Coupled Oscillators (Kuramoto Model)

```python
from synch_analysis import CoupledOscillatorDataSource, SynchronizationPipeline
import numpy as np

# Strong coupling - should synchronize
coupled = CoupledOscillatorDataSource(
    n_oscillators=2,
    coupling_strength=1.5,
    natural_freqs=[1.0, 1.05],  # Close frequencies
    dt=0.01,
    duration=100.0,
    noise_std=0.01,
    sampling_rate=100.0
)

pipeline = SynchronizationPipeline(coupled).run()
pipeline.plot_dashboard(sliding_window=200)
```

**Variants:**
```python
# Weak coupling - no synchronization
coupled_weak = CoupledOscillatorDataSource(
    coupling_strength=0.1,
    natural_freqs=[1.0, 1.05]
)

# Large frequency difference
coupled_large_diff = CoupledOscillatorDataSource(
    coupling_strength=2.0,
    natural_freqs=[1.0, 2.0]  # 2x difference
)

# With significant noise
coupled_noisy = CoupledOscillatorDataSource(
    coupling_strength=1.0,
    natural_freqs=[1.0, 1.02],
    noise_std=0.5
)

# More oscillators (uses first 2 for analysis)
coupled_5 = CoupledOscillatorDataSource(
    n_oscillators=5,
    coupling_strength=1.0,
    natural_freqs=np.random.normal(1.0, 0.1, 5)
)
```

---

### Belousov-Zhabotinsky Oscillator (Oregonator Model)

```python
from synch_analysis import BelousovZhabotinskyDataSource, SynchronizationPipeline

# Classic oscillatory regime with sensor delay
bz = BelousovZhabotinskyDataSource(
    f=1.0,
    q=0.05,
    eps=0.02,
    dt=0.01,
    initial_values=[0.1, 0.1],
    iterations=10000,
    variable="x",             # or "z"
    delay_steps=100,          # Simulated sensor delay (1s at 100 Hz)
    noise_std=0.05,           # Measurement noise
    sampling_rate=100.0,
    transient=2000,           # Discard initial transient
)

pipeline = SynchronizationPipeline(bz).run()
pipeline.plot_dashboard()

# Get statistics
stats = pipeline.get_stats()
print(f"Mean R: {stats['mean_R']:.4f}")
print(f"Sync ratio: {stats['sync_ratio']:.2%}")
```

**Variants:**
```python
# No delay - identical signals (single run copied)
bz_copy = BelousovZhabotinskyDataSource(
    iterations=5000,
    delay_steps=0,     # Creates copy of signal_a as signal_b
    noise_std=0.0
)

# Different Oregonator parameters
bz_strong = BelousovZhabotinskyDataSource(
    f=2.0,             # Higher stoichiometric parameter
    q=0.01,            # Smaller q
    eps=0.01,          # Stronger time-scale separation
    iterations=8000
)

# Extract z variable instead of x
bz_z = BelousovZhabotinskyDataSource(
    variable="z",
    iterations=5000
)

# Delay detection: sweep delay to find optimal sync lag
for delay in range(0, 300, 10):
    bz = BelousovZhabotinskyDataSource(
        iterations=3000,
        delay_steps=delay,
        noise_std=0.02,
        transient=500
    )
    pipeline = SynchronizationPipeline(bz).run()
    stats = pipeline.get_stats()
    print(f"Delay {delay:3d}: Mean R = {stats['mean_R']:.4f}")
```

---

### Parquet Data (Industrial/Experimental)

```python
from synch_analysis import ParquetDataSource, SynchronizationPipeline

# Industrial sensor data
parquet = ParquetDataSource(
    file_path="data/temperature_sensors.parquet",
    column_a="T_sensor_01",
    column_b="T_sensor_02",
    index_start=0,
    index_end=10000,
    window=60,              # 60-sample rolling mean
    lag=None,               # No time lag
    sampling_rate=1.0       # 1 Hz
)

pipeline = SynchronizationPipeline(parquet).run()
pipeline.plot_dashboard(sliding_window=50)
```

**With time lag analysis:**
```python
# Test different lags to find optimal synchronization
for lag in range(-10, 11):
    parquet_lag = ParquetDataSource(
        file_path="data/sensors.parquet",
        column_a="sensor_A",
        column_b="sensor_B",
        lag=lag,
        window=30
    )
    pipeline = SynchronizationPipeline(parquet_lag).run()
    stats = pipeline.get_stats()
    print(f"Lag {lag:3d}: Mean R = {stats['mean_R']:.4f}")
```

---

## Analysis Pipeline Examples

### Basic Analysis

```python
from synch_analysis import (
    LorenzDataSource, 
    SynchronizationPipeline,
    SynchronizationAnalyzer,
    SynchronizationVisualizer
)

# Using high-level pipeline
lorenz = LorenzDataSource(iterations=3000)
pipeline = SynchronizationPipeline(lorenz).run()

# Access components directly
analyzer = pipeline.analyzer
visualizer = pipeline.visualizer

# Get detailed statistics
stats = analyzer.get_summary_stats()
for key, value in stats.items():
    print(f"{key}: {value:.6f}")

# Access computed arrays
R_t = analyzer.order_parameter          # Kuramoto order parameter
phase_diff = analyzer.phase_diff        # Phase difference
phase_a = analyzer.phase_a              # Instantaneous phase A
phase_b = analyzer.phase_b              # Instantaneous phase B
```

---

### Custom Visualization

```python
from synch_analysis import LorenzDataSource, SynchronizationPipeline
import matplotlib.pyplot as plt
import numpy as np

lorenz = LorenzDataSource(iterations=5000)
pipeline = SynchronizationPipeline(lorenz).run()

# Create custom figure
fig, axes = plt.subplots(2, 2, figsize=(14, 10))

# 1. Raw signals (first 1000 samples)
pipeline.visualizer.plot_signals(axes[0, 0], n_samples=1000)
axes[0, 0].set_title("First 1000 samples")

# 2. Phase portrait
pipeline.visualizer.plot_phase_portrait(axes[0, 1])

# 3. Order parameter with sliding window
pipeline.visualizer.plot_order_parameter(axes[1, 0], sliding_window=100)

# 4. Phase difference
pipeline.visualizer.plot_phase_difference(axes[1, 1])

plt.tight_layout()
plt.show()
```

---

### Animation

```python
from synch_analysis import CoupledOscillatorDataSource, SynchronizationPipeline

coupled = CoupledOscillatorDataSource(
    coupling_strength=1.0,
    natural_freqs=[1.0, 1.02],
    duration=50.0
)

pipeline = SynchronizationPipeline(coupled).run()

# Create animation
anim = pipeline.animate(interval=30, trail_length=100)

# Save as GIF (requires imagemagick or pillow)
anim.save("phase_animation.gif", writer="pillow", fps=30)

# Or save as MP4 (requires ffmpeg)
# anim.save("phase_animation.mp4", writer="ffmpeg", fps=30)
```

---

### Batch Comparison

```python
from synch_analysis import (
    LorenzDataSource, SinusoidDataSource, CoupledOscillatorDataSource,
    BelousovZhabotinskyDataSource,
    compare_data_sources
)
import numpy as np

# Create multiple sources
sources = [
    LorenzDataSource(iterations=2000, variable="x"),
    LorenzDataSource(iterations=2000, variable="y"),
    SinusoidDataSource(frq_a=1.0, frq_b=1.0, pers=5, delay_b=3),
    SinusoidDataSource(frq_a=1.0, frq_b=1.05, pers=10),
    CoupledOscillatorDataSource(coupling_strength=0.5, natural_freqs=[1.0, 1.05]),
    CoupledOscillatorDataSource(coupling_strength=2.0, natural_freqs=[1.0, 1.05]),
    BelousovZhabotinskyDataSource(iterations=3000, delay_steps=50, transient=500),
]

labels = [
    "Lorenz (x)",
    "Lorenz (y)",
    "Sinusoid (sync, delay=3)",
    "Sinusoid (beat, 5% freq diff)",
    "Coupled (weak K=0.5)",
    "Coupled (strong K=2.0)",
    "BZ (delay=50)",
]

# Compare all sources
results_df = compare_data_sources(sources, labels)

# Display results
print(results_df.to_string(index=False))

# Plot comparison
import matplotlib.pyplot as plt
fig, ax = plt.subplots(figsize=(10, 6))
bars = ax.bar(range(len(results_df)), results_df['mean_R'])
ax.set_xticks(range(len(results_df)))
ax.set_xticklabels(results_df['source'], rotation=45, ha='right')
ax.set_ylabel('Mean Kuramoto Order Parameter R')
ax.set_title('Synchronization Comparison Across Data Sources')
ax.set_ylim(0, 1.1)

# Add value labels on bars
for bar, val in zip(bars, results_df['mean_R']):
    ax.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.02,
            f'{val:.3f}', ha='center', va='bottom')

plt.tight_layout()
plt.show()
```

---

### Parameter Sweep

```python
from synch_analysis import CoupledOscillatorDataSource, SynchronizationPipeline
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

# Sweep coupling strength
coupling_values = np.linspace(0.1, 3.0, 30)
results = []

for K in coupling_values:
    source = CoupledOscillatorDataSource(
        coupling_strength=K,
        natural_freqs=[1.0, 1.05],
        duration=50.0
    )
    pipeline = SynchronizationPipeline(source).run()
    stats = pipeline.get_stats()
    stats['coupling'] = K
    results.append(stats)

df = pd.DataFrame(results)

# Plot synchronization transition
plt.figure(figsize=(10, 6))
plt.plot(df['coupling'], df['mean_R'], 'b-o', label='Mean R')
plt.plot(df['coupling'], df['sync_ratio'], 'r-s', label='Sync Ratio (R>0.8)')
plt.axhline(y=0.8, color='g', linestyle='--', alpha=0.5, label='Threshold')
plt.xlabel('Coupling Strength K')
plt.ylabel('Synchronization Measure')
plt.title('Kuramoto Synchronization Transition')
plt.legend()
plt.grid(True, alpha=0.3)
plt.show()
```

---

## Export Examples

### Export All Results

```python
from synch_analysis import LorenzDataSource, SynchronizationPipeline, export_results

lorenz = LorenzDataSource(iterations=5000)
pipeline = SynchronizationPipeline(lorenz).run()

# Export everything
export_results(pipeline, "results/lorenz_full")

# Creates:
# results/lorenz_full/
# ├── sync_stats.csv      # Summary statistics
# ├── sync_timeseries.csv # Time series data
# └── sync_dashboard.png  # Dashboard figure
```

---

### Custom Export

```python
from synch_analysis import LorenzDataSource, SynchronizationPipeline
import pandas as pd
import matplotlib.pyplot as plt
from pathlib import Path

lorenz = LorenzDataSource(iterations=5000)
pipeline = SynchronizationPipeline(lorenz).run()

output_dir = Path("results/custom_export")
output_dir.mkdir(parents=True, exist_ok=True)

# 1. Export statistics as JSON
import json
with open(output_dir / "stats.json", "w") as f:
    json.dump(pipeline.get_stats(), f, indent=2)

# 2. Export time series with custom columns
analyzer = pipeline.analyzer
df = pd.DataFrame({
    "time": analyzer.signal_pair.time[:len(analyzer.order_parameter)],
    "R": analyzer.order_parameter,
    "phase_diff": analyzer.phase_diff,
    "phase_A": analyzer.phase_a,
    "phase_B": analyzer.phase_b,
    "amp_A": analyzer.amplitude_a,
    "amp_B": analyzer.amplitude_b,
})
df.to_csv(output_dir / "timeseries_full.csv", index=False)

# 3. Save high-res dashboard
fig = pipeline.plot_dashboard()
fig.savefig(output_dir / "dashboard_300dpi.png", dpi=300, bbox_inches="tight")
plt.close(fig)

# 4. Save individual plots
fig, axes = plt.subplots(2, 2, figsize=(12, 10))
pipeline.visualizer.plot_signals(axes[0, 0], n_samples=1000)
pipeline.visualizer.plot_phase_portrait(axes[0, 1])
pipeline.visualizer.plot_order_parameter(axes[1, 0], sliding_window=50)
pipeline.visualizer.plot_phase_difference(axes[1, 1])
fig.savefig(output_dir / "four_panel.png", dpi=150)
plt.close(fig)

print(f"Exported to {output_dir}")
```

---

## CLI Examples

```bash
# Lorenz attractor
synch-analysis lorenz --iterations 2000 --output results/lorenz --dashboard --stats

# Sinusoid with delay
synch-analysis sinusoid --delay-b 3 --pers 5 --output results/sinusoid --dashboard

# Coupled oscillators
synch-analysis coupled --coupling 1.5 --freqs 1.0 1.05 --duration 50 --output results/coupled

# Parquet data
synch-analysis parquet --file data/sensors.pqt --col-a T1 --col-b T2 --window 30 --output results/parquet

# Belousov-Zhabotinsky (Oregonator model)
synch-analysis bz --iterations 10000 --delay-steps 100 --noise 0.05 --output results/bz --dashboard

# JSON output for scripting
synch-analysis lorenz --iterations 1000 --stats --format json > stats.json
```

---

## Complete Notebook-Style Workflow

```python
# 1. Setup
from synch_analysis import *
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

# 2. Create data source
source = CoupledOscillatorDataSource(
    coupling_strength=1.2,
    natural_freqs=[1.0, 1.03],
    duration=100.0,
    noise_std=0.02
)

# 3. Run pipeline
pipeline = SynchronizationPipeline(source).run()

# 4. Analyze results
stats = pipeline.get_stats()
print("=== Synchronization Statistics ===")
for k, v in stats.items():
    print(f"  {k}: {v:.6f}")

# 5. Visualize
fig = pipeline.plot_dashboard(sliding_window=100, n_signal_samples=500)
plt.show()

# 6. Export
export_results(pipeline, "results/experiment_001")

# 7. Optional: Create animation
anim = pipeline.animate(interval=50, trail_length=200)
anim.save("results/experiment_001/phase_evolution.gif", writer="pillow", fps=20)
```

---

## Jupyter Notebook Integration

```python
# In Jupyter notebook
from synch_analysis import *

# Enable inline plotting
%matplotlib inline

# Run analysis
source = LorenzDataSource(iterations=3000)
pipeline = SynchronizationPipeline(source).run()

# Display dashboard inline
pipeline.plot_dashboard()

# Display stats as table
import pandas as pd
pd.DataFrame([pipeline.get_stats()]).T.style.format("{:.6f}")
```

---

## Industrial Data Notebooks (in `notebooks/`)

### Phase Synchronization Analysis (T11/T12 Temperatures)

```bash
# Open the notebooks from notebooks/ directory
jupyter notebook notebooks/kuramoto_jrp_analysis_T11_T12.ipynb
jupyter notebook notebooks/kuramoto_jrp_output_T11_T12.ipynb
```

These notebooks analyze synchronization between **FormacionMWEntT11TempPV** (MW inlet temperature T11) and **FormacionMWSalT12TempPV** (MW outlet temperature T12) from `../data/datos_ind.pqt` (relative to notebooks/).

**Analysis pipeline:**
1. **Hilbert transform** → Extract instantaneous phase
2. **Kuramoto order parameter** → Measure phase synchronization R(t) ∈ [0,1]
3. **Lag sweep** (±900s, step=10s) → Find optimal time delay
4. **Joint Recurrence Plots** (JRP) → State-space synchronization (RR, DET, LAM)

**Key metrics:**
| Metric | Range | Meaning |
|--------|-------|---------|
| `r_mean` | [0,1] | Mean Kuramoto order parameter |
| `frac_above_07` | [0,1] | Fraction of time with strong sync (R>0.7) |
| `max_sustained_sec` | [0,∞) | Longest continuous sync segment |
| `jrp_RR` | [0,1] | Joint Recurrence Rate |
| `jrp_DET` | [0,1] | Determinism (diagonal lines) |
| `jrp_LAM` | [0,1] | Laminarity (vertical lines) |

**Optimal lag criteria (updated):**
- **Kuramoto**: Combines fraction of time with strong phase sync (frac_above_07) and mean Kuramoto r (r_mean)
- **JRP**: Combined DET × LAM × RR score, excluding extreme lags (±max_lag)
- **Combined**: Arithmetic mean of both normalized scores

**Real lag (physical transit time):**
Each notebook computes the physical transit time between T11 and T12 at the end:
```python
lag = int(18600 / df['FormacionVelocidad'].loc[start_time:end_time].mean())
print(f'Real lag (|distance/speed|): {lag}s ({lag/60:.1f} min)')
```
This uses the belt/conveyor distance (18600 units) divided by the average `FormacionVelocidad` in the analysis window.

**Figure settings:**
All notebooks use publication-quality figure settings:
- White background
- No grid lines
- High DPI (300) suitable for journal publication
- Tight bounding box and minimal padding

```python
# Example: Load saved results (from notebooks/ directory)
results = pd.read_parquet('../data/kuramoto_lag_sweep_T11_T12.parquet')
jrp_results = pd.read_parquet('../data/kuramoto_jrp_lag_sweep_T11_T12.parquet')

# Find best lag (using updated criteria)
best_kuramoto = results.loc[results['kuramoto_score'].idxmax(), 'lag']
best_jrp = jrp_results.loc[jrp_results['jrp_score'].idxmax(), 'lag']
print(f"Best Kuramoto lag: {best_kuramoto}s")
print(f"Best JRP lag: {best_jrp}s")
```

### BZ Delayed Signal Analysis

```bash
jupyter notebook notebooks/kuramoto_jrp_analysis_bz_delayed.ipynb
jupyter notebook notebooks/kuramoto_jrp_output_bz_delayed.ipynb
```

These analyze synchronization between a BZ (Belousov-Zhabotinsky) signal and its delayed version using combined Kuramoto + JRP analysis.

**Analysis pipeline:**
1. **Hilbert transform** → Extract instantaneous phase
2. **Kuramoto order parameter** → Measure phase synchronization R(t) ∈ [0,1]
3. **Lag sweep** → Find optimal time delay
4. **Joint Recurrence Plots** (JRP) → State-space synchronization (RR, DET, LAM)

**Optimal lag criteria:**
- **Kuramoto**: Combines fraction of time with strong phase sync (frac_above_07) and mean Kuramoto r (r_mean)
- **JRP**: Combined DET × LAM × RR score, excluding extreme lags (±max_lag)
- **Combined**: Arithmetic mean of both normalized scores

**Data:** Results saved to `../data/kuramoto_jrp_lag_sweep_bz_delayed.parquet` (from notebooks/ directory).

**Figure settings:**
All notebooks use publication-quality figure settings:
- White background
- No grid lines
- High DPI (300) suitable for journal publication
- Tight bounding box and minimal padding

### Lorenz Delayed Signal Analysis

```bash
jupyter notebook notebooks/kuramoto_jrp_analysis_lorenz_delayed.ipynb
jupyter notebook notebooks/kuramoto_jrp_output_lorenz_delayed.ipynb
```

These analyze synchronization between a Lorenz x-variable and its delayed version (true delay: 150 steps = 1.5s at 100 Hz).

**Analysis pipeline:**
1. **Hilbert transform** → Extract instantaneous phase
2. **Kuramoto order parameter** → Measure phase synchronization R(t) ∈ [0,1]
3. **Lag sweep** (±300 steps, step=1) → Find optimal time delay
4. **Joint Recurrence Plots** (JRP) → State-space synchronization (RR, DET, LAM)

**Optimal lag criteria (updated):**
- **Kuramoto**: Combines fraction of time with strong phase sync (frac_above_07) and mean Kuramoto r (r_mean)
- **JRP**: Combined DET × LAM × RR score, excluding extreme lags (±max_lag)
- **Combined**: Arithmetic mean of both normalized scores

**True delay:** Known to be 150 steps (1.5s), used as ground truth for validation.

**Figure settings:**
All notebooks use publication-quality figure settings:
- White background
- No grid lines
- High DPI (300) suitable for journal publication