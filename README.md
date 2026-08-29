# synch_delay -  Synchronization Analysis

A unified Python framework for analyzing synchronization in time series data using the **Kuramoto order parameter** and **Joint Recurrence Plots (JRP)**.

## Features

- **Multiple Data Sources**: Experimental/industrial (Parquet), Lorenz attractor, Sinusoidal, Coupled Oscillators (Kuramoto model), Belousov-Zhabotinsky (Oregonator model)
- **Core Analysis**: Hilbert transform, Instantaneous phase, Kuramoto order parameter R(t), Phase difference
- **Delay Characterization**: Automated lag sweep combining Kuramoto phase synchronization and JRP state-space synchronization
- **Visualization**: Comprehensive dashboards, Phase portraits, Animations, Lag sweep plots
- **Batch Comparison**: Compare synchronization across different data types
- **Export**: CSV statistics, PNG dashboards, Time series data, Parquet results
- **CLI**: Command-line interface for quick analysis

## Installation

```bash
# Install in development mode
pip install -e .

# Or with dev dependencies
pip install -e ".[dev]"

# Install dependencies only
pip install -r requirements.txt
```

## Quick Start

### Python API

```python
from synch_analysis import LorenzDataSource, SynchronizationPipeline

# Lorenz attractor with sensor delay simulation
lorenz = LorenzDataSource(
    a=10.0, b=28.0, c=8.0/3.0,
    initial_values=[0.01, 0, 0.3],
    iterations=5000,
    delay_steps=150,   # 1.5s delay at 100 Hz sampling (applied to signal A)
    noise_std=0.05,    # optional measurement noise
    sampling_rate=100.0
)

# Run analysis pipeline
pipeline = SynchronizationPipeline(lorenz).run()
```

### Other Data Sources

```python
# Sinusoidal signals with phase delay
from synch_analysis import SinusoidDataSource
sin = SinusoidDataSource(frq_a=2, frq_b=2, delay_a=0, delay_b=3)
SynchronizationPipeline(sin).run().plot_dashboard()

# Coupled oscillators (Kuramoto model)
from synch_analysis import CoupledOscillatorDataSource
import numpy as np
coupled = CoupledOscillatorDataSource(coupling_strength=0.8, 
                                       natural_freqs=np.array([1.0, 1.05]),
                                       duration=50.0)
SynchronizationPipeline(coupled).run().plot_dashboard()

# Industrial data from Parquet
from synch_analysis import ParquetDataSource
parquet = ParquetDataSource("data/sensor.pqt", "varA", "varB")
SynchronizationPipeline(parquet).run().plot_dashboard()

# Belousov-Zhabotinsky oscillator (Oregonator model) with sensor delay
from synch_analysis import BelousovZhabotinskyDataSource
bz = BelousovZhabotinskyDataSource(
    f=1.0, q=0.05, eps=0.02,
    iterations=10000,
    delay_steps=100,   # Simulated sensor delay
    noise_std=0.05,
    sampling_rate=100.0
)
SynchronizationPipeline(bz).run().plot_dashboard()

# Delay characterization (find optimal lag)
from synch_analysis import DelayCharacterizationPipeline
delay_pipeline = DelayCharacterizationPipeline(
    lorenz,
    max_lag=300,
    lag_step=1,
    jrp_m=3, jrp_tau=1, jrp_rate=0.05, jrp_smooth_size=5
).run()

# Plot results
delay_pipeline.plot_kuramoto(true_delay_sec=1.5)
delay_pipeline.plot_jrp(true_delay_sec=1.5)
delay_pipeline.plot_combined(true_delay_sec=1.5)
```

## Data Sources

| Source | Description | Parameters |
|--------|-------------|------------|
| `ParquetDataSource` | Industrial/experimental sensor data from Parquet files | `file_path`, `column_a`, `column_b`, `index_start`, `index_end`, `window`, `lag`, `sampling_rate` |
| `LorenzDataSource` | Lorenz attractor with sensor delay simulation | `a`, `b`, `c`, `dt`, `initial_values`, `iterations`, `variable`, `delay_steps`, `noise_std`, `sampling_rate` |
| `SinusoidDataSource` | Sinusoidal signals with controllable phase/frequency/delay | `ph0_a`, `ph0_b`, `frq_a`, `frq_b`, `pers`, `delay_a`, `delay_b`, `iterations`, `sampling_rate` |
| `CoupledOscillatorDataSource` | Kuramoto model coupled oscillators | `n_oscillators`, `coupling_strength`, `natural_freqs`, `dt`, `duration`, `noise_std`, `sampling_rate` |
| `BelousovZhabotinskyDataSource` | Belousov-Zhabotinsky (Oregonator) with sensor delay | `f`, `q`, `eps`, `dt`, `initial_values`, `iterations`, `variable`, `delay_steps`, `noise_std`, `sampling_rate`, `transient` |

## CLI Usage

```bash
# Lorenz attractor with sensor delay
synch-analysis lorenz --iterations 5000 --delay-steps 150 --noise 0.05 --output results/

# Lorenz attractor (no delay, single signal copied)
synch-analysis lorenz --iterations 1000 --output results/

# Sinusoidal signals with phase delay
synch-analysis sinusoid --delay-b 3 --output results/

# Coupled oscillators
synch-analysis coupled --coupling 0.8 --freqs 1.0 1.05 --duration 50 --output results/

# Parquet data
synch-analysis parquet --file data.pqt --col-a varA --col-b varB --output results/
  
# Delay characterization (Optimal lag search)
synch-analysis delay --file data.pqt --col-a varA --col-b varB --max-lag 600 --output results/
  
# Belousov-Zhabotinsky (Oregonator model)
synch-analysis bz --iterations 10000 --delay-steps 100 --noise 0.05 --output results/
```

### CLI Options

```
synch-analysis [lorenz|sinusoid|coupled|parquet|bz|delay] [OPTIONS]

Common options:
  --output, -o        Output directory (default: results)
  --stats             Print statistics
  --format            Output format: json|csv (default: json)

Lorenz:
  --a, --b, --c       Lorenz parameters (default: 10, 28, 2.667)
  --dt                Time step (default: 0.01)
  --x, --y, --z       Initial values (default: 0.01, 0, 0.3)
  --iterations        Number of iterations (default: 1000)
  --variable          Variable to extract: x|y|z (default: x)
  --sampling-rate     Sampling rate in Hz (default: 100)
  --delay-steps       Sensor delay in time steps (default: 0)
  --noise             Measurement noise std (default: 0)

Sinusoid:
  --ph0-a, --ph0-b    Initial phases (default: 0)
  --frq-a, --frq-b    Frequencies (default: 1)
  --pers              Number of periods (default: 1)
  --delay-a, --delay-b Delays (default: 0)

Coupled:
  --coupling          Coupling strength K (default: 0.5)
  --freqs             Natural frequencies (space-separated, default: 1.0 1.05)
  --duration          Simulation duration (default: 100)
  --dt                Time step (default: 0.01)
  --noise             Noise standard deviation (default: 0)

Parquet:
  --file              Parquet file path
  --col-a, --col-b    Column names
  --start, --end      Index range (int for positional, str for timestamp)
  --window            Rolling window size (default: 60, use 1 for no smoothing)
  --lag               Time lag between signals

BZ:
  --f                 Stoichiometric parameter (default: 1.0)
  --q                 Small parameter (default: 0.05)
  --eps               Time-scale separation parameter (default: 0.02)
  --dt                Integration time step (default: 0.01)
  --x0, --z0          Initial values (default: 0.1, 0.1)
  --iterations        Number of integration steps (default: 10000)
  --variable          Variable to extract: x|z (default: x)
  --delay-steps       Sensor delay in time steps (default: 100)
  --noise             Measurement noise std (default: 0.05)
  --transient         Transient steps to discard (default: 2000)

Delay:
  --max-lag           Maximum lag to sweep (default: 100)
  --lag-step          Lag step size (default: 1)
  --jrp-m             Embedding dimension (default: 3)
  --jrp-tau           Embedding delay (default: 1)
  --jrp-rate          Recurrence rate (default: 0.05)
  --jrp-smooth-size   Smoothing window for JRP (default: 5)
```

## Project Structure

```
synch_delay/
├── src/synch_analysis/    # Main package
│   ├── __init__.py        # Public API
│   ├── core.py            # Core data structures (SignalPair, DataSource)
│   ├── sources.py         # Data source implementations
│   ├── analyzer.py        # SynchronizationAnalyzer
│   ├── visualizer.py      # SynchronizationVisualizer
│   ├── pipeline.py        # SynchronizationPipeline, DelayCharacterizationPipeline, batch comparison
│   ├── jrp.py             # Joint Recurrence Plot functions
│   └── cli.py             # Command-line interface
├── notebooks/             # Example notebooks
│   ├── synch_analysis_unified.ipynb            # Complete framework demo
│   ├── delay_char_industrial.ipynb             # Industrial delay characterization
│   ├── delay_char_lorenz_delayed.ipynb         # Lorenz delay characterization
│   ├── delay_char_bz_delayed.ipynb             # BZ delay characterization
│   ├── kuramoto_jrp_analysis_varA_varB.ipynb   # varA/varB combined Kuramoto+JRP
│   ├── kuramoto_jrp_analysis_bz_delayed.ipynb  # BZ delayed JRP analysis
│   ├── kuramoto_jrp_analysis_lorenz_delayed.ipynb # Lorenz delayed JRP analysis
│   └── kuramoto_jrp_output_*.ipynb             # Executable output notebooks
├── data/                  # Data files (Parquet, etc.)
├── results/               # Analysis outputs
├── requirements.txt
├── pyproject.toml
└── README.md
```

## Example Notebooks

See `notebooks/` for complete examples:

```bash
jupyter notebook notebooks/
```

Available notebooks:
- `synch_analysis_unified.ipynb` - Complete framework demo
- `delay_char_industrial.ipynb` - Industrial delay characterization (Parquet data)
- `delay_char_lorenz_delayed.ipynb` - Lorenz delay characterization
- `delay_char_bz_delayed.ipynb` - BZ delay characterization
- `kuramoto_jrp_analysis_varA_varB.ipynb` - varA/varB combined Kuramoto + JRP analysis
- `kuramoto_jrp_analysis_bz_delayed.ipynb` - BZ delayed JRP analysis
- `kuramoto_jrp_analysis_lorenz_delayed.ipynb` - Lorenz delayed signal analysis

**All JRP notebooks include real lag calculation:** Physical transport delay computed and marked on plots for comparison with optimal synchronization lag.

**Analysis criteria (updated):**
- **Kuramoto**: Combines fraction of time with strong phase sync (frac_above_07) and mean Kuramoto r (r_mean)
- **JRP**: Normalized Recurrence Rate (RR) as sole criterion, excluding extreme lags (±max_lag)
- **Combined**: Arithmetic mean of both normalized scores

**Figure settings:**
- Publication-quality figures with white background
- No grid lines
- High DPI (300) suitable for journal publication
- Tight bounding box and minimal padding

## Results Interpretation

| Metric | Range | Interpretation |
|--------|-------|----------------|
| R(t) | [0, 1] | 1 = perfect sync, 0 = no sync |
| mean_R | [0, 1] | Average synchronization level |
| sync_ratio | [0, 1] | Fraction of time with R > 0.8 |
| phase_diff | [-π, π] | Phase lag between signals |
| jrp_RR | [0, 1] | Joint Recurrence Rate |
| jrp_DET | [0, 1] | Determinism (diagonal lines) |
| jrp_LAM | [0, 1] | Laminarity (vertical lines) |

## Export Formats

The `export_results()` function creates:
- `sync_stats.csv` - Summary statistics
- `sync_timeseries.csv` - Time series data (R, phases, phase diff)
- `sync_dashboard.png` - Full dashboard visualization

## License

Apache 2.0 License