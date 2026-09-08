# Usage Examples

Complete usage examples for `synch_analysis`.

---

## Quick Start: Delay Characterization (Primary Pipeline)

```python
from synch_analysis import LorenzDataSource, DelayCharacterizationPipeline

# Lorenz attractor with sensor delay simulation
lorenz = LorenzDataSource(
    a=10.0, b=28.0, c=8.0/3.0,
    initial_values=[0.01, 0, 0.3],
    iterations=5000,
    delay_steps=150,   # 1.5s delay at 100 Hz sampling
    noise_std=0.05,    # optional measurement noise
    sampling_rate=100.0
)

# Run delay characterization pipeline
pipeline = DelayCharacterizationPipeline(
    lorenz,
    max_lag=300,
    lag_step=1,
    jrp_m=3, jrp_tau=1, jrp_rate=0.05, jrp_smooth_size=5
).run()

# Get optimal lags
opt = pipeline.get_optimal_lags()
print(f"Best Kuramoto lag: {opt['best_kuramoto_lag']} steps")
print(f"Best JRP lag: {opt['best_jrp_lag']} steps")
print(f"Best Combined lag: {opt['best_combined_lag']} steps")

# View plots with true delay marker
pipeline.plot_kuramoto(true_delay_sec=1.5)
pipeline.plot_jrp(true_delay_sec=1.5)
pipeline.plot_combined(true_delay_sec=1.5)

# Export all results
pipeline.export_results("results/lorenz_delay")
```

---

## Quick Start: Synchronization Analysis

```python
from synch_analysis import LorenzDataSource, SynchronizationPipeline

# Lorenz attractor with sensor delay simulation
lorenz = LorenzDataSource(
    a=10.0, b=28.0, c=8.0/3.0,
    initial_values=[0.01, 0, 0.3],
    iterations=5000,
    delay_steps=150,   # 1.5s delay at 100 Hz sampling
    noise_std=0.05,
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
from synch_analysis import LorenzDataSource, DelayCharacterizationPipeline
import numpy as np

# Classic chaotic regime with sensor delay - DELAY CHARACTERIZATION
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

pipeline = DelayCharacterizationPipeline(
    lorenz,
    max_lag=300,
    lag_step=1,
    jrp_m=3, jrp_tau=1, jrp_rate=0.05, jrp_smooth_size=5
).run()

# Plot with true delay
pipeline.plot_combined(true_delay_sec=1.5)
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
    pipeline = DelayCharacterizationPipeline(
        lorenz,
        max_lag=300,
        lag_step=5,
        jrp_m=3, jrp_tau=1, jrp_rate=0.05, jrp_smooth_size=5
    ).run()
    opt = pipeline.get_optimal_lags()
    print(f"True delay {delay:3d}: Combined lag = {opt['best_combined_lag']:4d}")
```

**Lag Convention:**
- `delay_steps=150` means signal A is delayed by 150 steps relative to signal B
- The pipeline will find optimal lag = -150 to align the signals
- `true_delay_sec = -delay_steps / sampling_rate` for plotting

---

### Sinusoidal Signals

```python
from synch_analysis import SinusoidDataSource, DelayCharacterizationPipeline
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

pipeline = DelayCharacterizationPipeline(sinusoid, max_lag=50).run()
pipeline.plot_combined()
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
from synch_analysis import CoupledOscillatorDataSource, DelayCharacterizationPipeline
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

pipeline = DelayCharacterizationPipeline(coupled, max_lag=100).run()
pipeline.plot_combined()
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
from synch_analysis import BelousovZhabotinskyDataSource, DelayCharacterizationPipeline

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

pipeline = DelayCharacterizationPipeline(bz, max_lag=300).run()
pipeline.plot_combined()

# Get statistics
opt = pipeline.get_optimal_lags()
print(f"Best Combined lag: {opt['best_combined_lag']} steps")
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
    pipeline = DelayCharacterizationPipeline(
        bz,
        max_lag=300,
        lag_step=5,
        jrp_m=3, jrp_tau=1, jrp_rate=0.05, jrp_smooth_size=5
    ).run()
    opt = pipeline.get_optimal_lags()
    print(f"Delay {delay:3d}: Best combined lag = {opt['best_combined_lag']:4d}")
```

**Lag Convention:**
- `delay_steps=100` means signal A is delayed by 100 steps relative to signal B
- The pipeline will find optimal lag = -100 to align the signals

---

### Parquet Data (Industrial/Experimental)

```python
from synch_analysis import ParquetDataSource, DelayCharacterizationPipeline

# Industrial sensor data - DELAY CHARACTERIZATION
parquet = ParquetDataSource(
    file_path="data/sensors.parquet",
    column_a="sensor_A",
    column_b="sensor_B",
    index_start=0,
    index_end=10000,
    window=60,              # 60-sample rolling mean
    lag=None,               # No time lag
    sampling_rate=1.0       # 1 Hz
)

pipeline = DelayCharacterizationPipeline(
    parquet,
    max_lag=500,
    lag_step=5,
    jrp_m=5,
    jrp_tau=1,
    jrp_rate=0.3,
    jrp_smooth_size=5,
).run()

# Plot with true delay marker (in seconds)
pipeline.plot_kuramoto(true_delay_sec=90)
pipeline.plot_jrp(true_delay_sec=90)
pipeline.plot_combined(true_delay_sec=90)
```

**Timestamp-based slicing:**
```python
# Slice by timestamp (auto-detects datetime column)
parquet = ParquetDataSource(
    file_path="data/sensors.parquet",
    column_a="sensor_A",
    column_b="sensor_B",
    index_start="2021-11-03 12:10:00",
    index_end="2021-11-03 12:30:00",
    window=1,               # No smoothing in data source
    lag=None,
    sampling_rate=1.0
)

pipeline = DelayCharacterizationPipeline(
    parquet,
    max_lag=500,
    lag_step=5
).run()
```

**With time lag analysis (manual):**
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

**For automated delay characterization, use `DelayCharacterizationPipeline`:**
```python
from synch_analysis import DelayCharacterizationPipeline

pipeline = DelayCharacterizationPipeline(
    parquet,
    max_lag=500,
    lag_step=5,
    jrp_m=5,
    jrp_tau=1,
    jrp_rate=0.3,
    jrp_smooth_size=5,
).run()

# Plot with true delay marker (in seconds)
pipeline.plot_kuramoto(true_delay_sec=90)
pipeline.plot_jrp(true_delay_sec=90)
pipeline.plot_combined(true_delay_sec=90)
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

### Delay Characterization Sweep (Systematic Validation)

```python
from synch_analysis import (
    LorenzDataSource, DelayCharacterizationPipeline
)
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

# Sweep delay steps to find true delay
delay_values = range(0, 300, 10)
results = []

for delay in delay_values:
    source = LorenzDataSource(
        delay_steps=delay,
        noise_std=0.02,
        iterations=2000
    )
    pipeline = DelayCharacterizationPipeline(
        source,
        max_lag=300,
        lag_step=5,
        jrp_m=3, jrp_tau=1, jrp_rate=0.05, jrp_smooth_size=5
    ).run()
    
    opt = pipeline.get_optimal_lags()
    stats = pipeline.get_results()
    
    results.append({
        'true_delay': -delay,  # Pipeline convention: negative
        'best_kuramoto': opt['best_kuramoto_lag'],
        'best_jrp': opt['best_jrp_lag'],
        'best_combined': opt['best_combined_lag'],
    })

df = pd.DataFrame(results)

# Plot delay detection accuracy
plt.figure(figsize=(10, 6))
plt.plot(-df['true_delay'], df['best_kuramoto'], 'b-o', label='Kuramoto')
plt.plot(-df['true_delay'], df['best_jrp'], 'r-s', label='JRP')
plt.plot(-df['true_delay'], df['best_combined'], 'k-^', label='Combined')
plt.plot([-300, 0], [-300, 0], 'k--', alpha=0.5, label='Perfect')
plt.xlabel('True Delay (steps)')
plt.ylabel('Estimated Delay (steps)')
plt.title('Delay Detection Accuracy')
plt.legend()
plt.grid(True, alpha=0.3)
plt.show()
```

---

## Export Examples

### Export All Results (SynchronizationPipeline)

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

### Delay Characterization Export

```python
from synch_analysis import DelayCharacterizationPipeline, LorenzDataSource

lorenz = LorenzDataSource(delay_steps=150, iterations=5000)
pipeline = DelayCharacterizationPipeline(
    lorenz,
    max_lag=300, lag_step=1,
    jrp_m=3, jrp_tau=1, jrp_rate=0.05, jrp_smooth_size=5
).run()

# Export all results
pipeline.export_results("results/lorenz_delay")

# Creates:
# results/lorenz_delay/
# ├── lag_sweep_results.parquet      # Full combined results
# ├── kuramoto_lag_sweep.parquet     # Kuramoto metrics
# ├── jrp_lag_sweep.parquet          # JRP metrics
# ├── kuramoto_scores.png            # Kuramoto plots
# ├── jrp_scores.png                 # JRP plots
# ├── combined_scores.png            # Combined plots
# └── delay_summary.txt              # Text summary
```

---

## CLI Examples

```bash
# Delay characterization - PRIMARY COMMAND (uses DelayCharacterizationPipeline)
synch-analysis delay --source-type parquet --file data/sensors.pqt --col-a varA --col-b varB --max-lag 600 --output results/delay

# Lorenz attractor with sensor delay (delay characterization mode)
synch-analysis delay --source-type lorenz --iterations 5000 --delay-steps 150 --max-lag 300 --output results/lorenz_delay

# Lorenz attractor (synchronization analysis mode)
synch-analysis lorenz --iterations 2000 --output results/lorenz --dashboard --stats

# Sinusoid with delay
synch-analysis sinusoid --delay-b 3 --pers 5 --output results/sinusoid --dashboard

# Coupled oscillators
synch-analysis coupled --coupling 1.5 --freqs 1.0 1.05 --duration 50 --output results/coupled

# Parquet data
synch-analysis parquet --file data/sensors.pqt --col-a varA --col-b varB --window 30 --output results/parquet

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

# 3. Run DELAY CHARACTERIZATION pipeline (primary)
pipeline = DelayCharacterizationPipeline(
    source,
    max_lag=200,
    lag_step=1,
    jrp_m=3, jrp_tau=1, jrp_rate=0.05, jrp_smooth_size=5
).run()

# 4. Analyze results
opt = pipeline.get_optimal_lags()
print("=== Optimal Lags ===")
for k, v in opt.items():
    print(f"  {k}: {v} steps ({v/100:.3f}s at 100 Hz)")

# 5. Visualize
fig = pipeline.plot_combined()
plt.show()

# 6. Export
pipeline.export_results("results/experiment_001")
```

---

## Jupyter Notebook Integration

```python
# In Jupyter notebook
from synch_analysis import *

# Enable inline plotting
%matplotlib inline

# Run DELAY CHARACTERIZATION
source = LorenzDataSource(iterations=3000, delay_steps=150)
pipeline = DelayCharacterizationPipeline(source, max_lag=300).run()

# Display dashboard inline
pipeline.plot_combined(true_delay_sec=1.5)

# Display stats as table
import pandas as pd
pd.DataFrame([pipeline.get_optimal_lags()]).T.style.format("{:.0f}")
```

---

## Industrial Data Notebooks (in `notebooks/`)

### Phase Synchronization Analysis (varA/varB)

```bash
# Open the notebooks from notebooks/ directory
jupyter notebook notebooks/delay_char_industrial.ipynb
jupyter notebook notebooks/kuramoto_jrp_analysis_varA_varB.ipynb
```

These notebooks analyze synchronization between **VarA** and **VarB** from `../data/datos_ind.pqt` (relative to notebooks/).

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
- **JRP**: Normalized Recurrence Rate (RR) as sole criterion, excluding extreme lags (±max_lag)
- **Combined**: Arithmetic mean of both normalized scores

**Real lag (physical transit time):**
Each notebook computes the physical transit time between VarA and VarB at the end:
```python
lag = int(18600 / df['Velocidad'].loc[start_time:end_time].mean())
print(f'Real lag (|distance/speed|): {lag}s ({lag/60:.1f} min)')
```
This uses the belt/conveyor distance (18600 units) divided by the average `Velocidad` in the analysis window.

**Figure settings:**
All notebooks use publication-quality figure settings:
- White background
- No grid lines
- High DPI (300) suitable for journal publication
- Tight bounding box and minimal padding

```python
# Example: Load saved results (from notebooks/ directory)
results = pd.read_parquet('../data/kuramoto_lag_sweep_varA_varB.parquet')
jrp_results = pd.read_parquet('../data/kuramoto_jrp_lag_sweep_varA_varB.parquet')

# Find best lag (using updated criteria)
best_kuramoto = results.loc[results['kuramoto_score'].idxmax(), 'lag']
best_jrp = jrp_results.loc[jrp_results['jrp_score'].idxmax(), 'lag']
print(f"Best Kuramoto lag: {best_kuramoto}s")
print(f"Best JRP lag: {best_jrp}s")
```

---

### Cross-Correlation & Mutual Information Delay Characterization (Industrial)

```bash
jupyter notebook notebooks/delay_char_crosscorr_mi_industrial.ipynb
```

Analyzes delay characterization using cross-correlation and mutual information as alternative methods to Kuramoto+JRP.

**Analysis pipeline:**
1. **Cross-correlation** → Find lag maximizing correlation
2. **Mutual Information** → Find lag maximizing MI (nonlinear dependency)
3. **Comparison** → Compare with Kuramoto+JRP results

**Key metrics:**
- Cross-correlation peak lag
- Mutual information peak lag
- Comparison with physical transit time

---

### BZ Delayed Signal Analysis

```bash
jupyter notebook notebooks/delay_char_bz_delayed.ipynb
jupyter notebook notebooks/kuramoto_jrp_analysis_bz_delayed.ipynb
```

These analyze synchronization between a BZ (Belousov-Zhabotinsky) signal and its delayed version using combined Kuramoto + JRP analysis.

**Analysis pipeline:**
1. **Hilbert transform** → Extract instantaneous phase
2. **Kuramoto order parameter** → Measure phase synchronization R(t) ∈ [0,1]
3. **Lag sweep** → Find optimal time delay
4. **Joint Recurrence Plots** (JRP) → State-space synchronization (RR, DET, LAM)

**Optimal lag criteria:**
- **Kuramoto**: Combines fraction of time with strong phase sync (frac_above_07) and mean Kuramoto r (r_mean)
- **JRP**: Normalized Recurrence Rate (RR) as sole criterion, excluding extreme lags (±max_lag)
- **Combined**: Arithmetic mean of both normalized scores

**Data:** Results saved to `../data/kuramoto_jrp_lag_sweep_bz_delayed.parquet` (from notebooks/ directory).

**Figure settings:**
All notebooks use publication-quality figure settings:
- White background
- No grid lines
- High DPI (300) suitable for journal publication
- Tight bounding box and minimal padding

---

### Cross-Correlation & Mutual Information Delay Characterization (BZ)

```bash
jupyter notebook notebooks/delay_char_crosscorr_mi_bz.ipynb
```

Analyzes delay characterization using cross-correlation and mutual information on BZ delayed signals.

---

### Lorenz Delayed Signal Analysis

```bash
jupyter notebook notebooks/delay_char_lorenz_delayed.ipynb
jupyter notebook notebooks/kuramoto_jrp_analysis_lorenz_delayed.ipynb
```

These analyze synchronization between a Lorenz x-variable and its delayed version (true delay: 150 steps = 1.5s at 100 Hz).

**Analysis pipeline:**
1. **Hilbert transform** → Extract instantaneous phase
2. **Kuramoto order parameter** → Measure phase synchronization R(t) ∈ [0,1]
3. **Lag sweep** (±300 steps, step=1) → Find optimal time delay
4. **Joint Recurrence Plots** (JRP) → State-space synchronization (RR, DET, LAM)

**Optimal lag criteria (updated):**
- **Kuramoto**: Combines fraction of time with strong phase sync (frac_above_07) and mean Kuramoto r (r_mean)
- **JRP**: Normalized Recurrence Rate (RR) as sole criterion, excluding extreme lags (±max_lag)
- **Combined**: Arithmetic mean of both normalized scores

**True delay:** Known to be 150 steps (1.5s), used as ground truth for validation.

**Figure settings:**
All notebooks use publication-quality figure settings:
- White background
- No grid lines
- High DPI (300) suitable for journal publication

---

### Cross-Correlation & Mutual Information Delay Characterization (Lorenz)

```bash
jupyter notebook notebooks/delay_char_crosscorr_mi_lorenz.ipynb
```

Analyzes delay characterization using cross-correlation and mutual information on Lorenz delayed signals.

---

### Results & Output Notebooks

```bash
jupyter notebook notebooks/kuramoto_jrp_output_varA_varB.ipynb
jupyter notebook notebooks/kuramoto_jrp_output_bz_delayed.ipynb
jupyter notebook notebooks/kuramoto_jrp_output_lorenz_delayed.ipynb
```

These notebooks load and visualize results from the analysis notebooks:
- Load saved Parquet results
- Create publication-quality figures
- Compare optimal lags with true delays
- Generate summary tables

---

### Method Comparison Notebooks

```bash
jupyter notebook notebooks/compare_methods_industrial.ipynb
jupyter notebook notebooks/compare_methods_bz.ipynb
jupyter notebook notebooks/compare_methods_lorenz.ipynb
```

Compare multiple delay characterization methods side-by-side:
- **Kuramoto + JRP** (primary pipeline)
- **Cross-correlation** (linear)
- **Mutual Information** (nonlinear)
- **Physical/real lag** (ground truth)

**Output:** Comparison tables and visualizations showing accuracy of each method.