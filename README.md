# synch_analysis - Unified Synchronization Analysis

A unified Python framework for analyzing synchronization in time series data using the **Kuramoto order parameter**.

## Features

- **Multiple Data Sources**: Experimental/industrial (Parquet), Lorenz attractor, Sinusoidal, Coupled Oscillators (Kuramoto model)
- **Core Analysis**: Hilbert transform, Instantaneous phase, Kuramoto order parameter R(t), Phase difference
- **Visualization**: Comprehensive dashboards, Phase portraits, Animations
- **Batch Comparison**: Compare synchronization across different data types
- **Export**: CSV statistics, PNG dashboards, Time series data
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

# Lorenz attractor with two nearby initial conditions
lorenz = LorenzDataSource(
    a=10.0, b=28.0, c=8.0/3.0,
    initial_values_1=[0.01, 0, 0.3],
    initial_values_2=[0.2, 0.1, 0.4],
    iterations=1000
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
export_results(pipeline, "results/")
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
parquet = ParquetDataSource("data/sensor.pqt", "Temp_T11", "Temp_T12")
SynchronizationPipeline(parquet).run().plot_dashboard()
```

## Data Sources

| Source | Description | Parameters |
|--------|-------------|------------|
| `ParquetDataSource` | Industrial/experimental sensor data from Parquet files | `file_path`, `column_a`, `column_b`, `index_start`, `index_end`, `window`, `lag` |
| `LorenzDataSource` | Lorenz attractor with configurable parameters | `a`, `b`, `c`, `dt`, `initial_values_1`, `initial_values_2`, `iterations`, `variable` |
| `SinusoidDataSource` | Sinusoidal signals with controllable phase/frequency/delay | `ph0_a`, `ph0_b`, `frq_a`, `frq_b`, `pers`, `delay_a`, `delay_b` |
| `CoupledOscillatorDataSource` | Kuramoto model coupled oscillators | `n_oscillators`, `coupling_strength`, `natural_freqs`, `dt`, `duration`, `noise_std` |

## CLI Usage

```bash
# Lorenz attractor
synch-analysis lorenz --iterations 1000 --output results/

# Sinusoidal signals with phase delay
synch-analysis sinusoid --delay-b 3 --output results/

# Coupled oscillators
synch-analysis coupled --coupling 0.8 --freqs 1.0 1.05 --duration 50 --output results/

# Parquet data
synch-analysis parquet --file data.pqt --col-a Temp1 --col-b Temp2 --output results/
```

### CLI Options

```
synch-analysis [lorenz|sinusoid|coupled|parquet] [OPTIONS]

Common options:
  --output, -o        Output directory (default: results)
  --stats             Print statistics
  --format            Output format: json|csv (default: json)

Lorenz:
  --a, --b, --c       Lorenz parameters (default: 10, 28, 2.667)
  --dt                Time step (default: 0.01)
  --x1, --y1, --z1    Initial values 1 (default: 0.01, 0, 0.3)
  --x2, --y2, --z2    Initial values 2 (default: 0.2, 0.1, 0.4)
  --iterations        Number of iterations (default: 1000)
  --variable          Variable to extract: x|y|z (default: x)
  --sampling-rate     Sampling rate in Hz (default: 100)

Sinusoid:
  --ph0-a, --ph0-b    Initial phases (default: 0)
  --frq-a, --frq-b    Frequencies (default: 1)
  --pers              Number of periods (default: 1)
  --delay-a, --delay-b Delays (default: 0)

Coupled:
  --coupling          Coupling strength K (default: 0.5)
  --freqs             Natural frequencies (space-separated, default: 1.0 1.05)
  --duration          Simulation duration (default: 100)
  --noise             Noise standard deviation (default: 0)

Parquet:
  --file              Parquet file path
  --col-a, --col-b    Column names
  --start, --end      Index range
  --window            Rolling window size (default: 60)
  --lag               Time lag between signals
```

## Project Structure

```
synch_agents/
├── src/synch_analysis/    # Main package
│   ├── __init__.py        # Public API
│   ├── core.py            # Core data structures (SignalPair, DataSource)
│   ├── sources.py         # Data source implementations
│   ├── analyzer.py        # SynchronizationAnalyzer
│   ├── visualizer.py      # SynchronizationVisualizer
│   ├── pipeline.py        # SynchronizationPipeline, batch comparison
│   └── cli.py             # Command-line interface
├── notebooks/             # Example notebooks
├── data/                  # Data files (Parquet, etc.)
├── results/               # Analysis outputs
├── old/                   # Original notebooks (archived)
├── kuramoto_sync_analysis_T11_T12.ipynb     # T11/T12 phase sync analysis
├── kuramoto_sync_output_T11_T12.ipynb       # T11/T12 executable output
├── kuramoto_jrp_analysis_T11_T12.ipynb      # T11/T12 combined Kuramoto+JRP
├── kuramoto_jrp_output_T11_T12.ipynb        # T11/T12 combined output
├── kuramoto_sync_analysis.ipynb             # Original NIR/MW humidity
├── kuramoto_sync_output.ipynb               # Original executable
├── kuramoto_jrp_analysis.ipynb              # Original combined
├── kuramoto_jrp_output.ipynb                # Original combined output
├── synch_analysis_unified.ipynb             # Complete framework demo
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
- `lorenz_analysis.ipynb` - Lorenz attractor synchronization
- `sinusoid_analysis.ipynb` - Sinusoidal signal analysis
- `coupled_oscillators.ipynb` - Kuramoto model oscillators
- `synch_analysis_unified.ipynb` - Complete framework demo

**Industrial data analysis (root directory):**
- `kuramoto_sync_analysis_T11_T12.ipynb` - Phase sync: T11/T12 temperatures (MW inlet/outlet)
- `kuramoto_sync_output_T11_T12.ipynb` - Executable output version
- `kuramoto_jrp_analysis_T11_T12.ipynb` - Combined Kuramoto + JRP analysis
- `kuramoto_jrp_output_T11_T12.ipynb` - Executable output version
- `kuramoto_sync_analysis.ipynb` - Original: NIR Humidity / MW Humidity
- `kuramoto_jrp_analysis.ipynb` - Original combined analysis

**All T11/T12 notebooks include real lag calculation:** Each notebook computes the physical transport delay using `lag = distance / mean(FormacionVelocidad)` (18600 units / belt speed) for comparison with the optimal synchronization lag found by Kuramoto/JRP analysis.

### Industrial Data Analysis (Root directory)

Additional notebooks for industrial temperature synchronization analysis using Hilbert + Kuramoto + Joint Recurrence Plots:

| Notebook | Data Source | Variables | Description |
|----------|-------------|-----------|-------------|
| `kuramoto_sync_analysis_T11_T12.ipynb` | `data/datos_ind.pqt` | FormacionMWEntT11TempPV, FormacionMWSalT12TempPV | Phase sync analysis (Hilbert + Kuramoto) |
| `kuramoto_sync_output_T11_T12.ipynb` | `data/datos_ind.pqt` | FormacionMWEntT11TempPV, FormacionMWSalT12TempPV | Executable output version |
| `kuramoto_jrp_analysis_T11_T12.ipynb` | `data/datos_ind.pqt` | FormacionMWEntT11TempPV, FormacionMWSalT12TempPV | Combined Kuramoto + JRP analysis |
| `kuramoto_jrp_output_T11_T12.ipynb` | `data/datos_ind.pqt` | FormacionMWEntT11TempPV, FormacionMWSalT12TempPV | Combined analysis output |

Original analysis (NIR Humidity / MW Humidity):
- `kuramoto_sync_analysis.ipynb` - Phase sync analysis
- `kuramoto_sync_output.ipynb` - Executable output
- `kuramoto_jrp_analysis.ipynb` - Combined Kuramoto + JRP
- `kuramoto_jrp_output.ipynb` - Combined output

## Results Interpretation

| Metric | Range | Interpretation |
|--------|-------|----------------|
| R(t) | [0, 1] | 1 = perfect sync, 0 = no sync |
| mean_R | [0, 1] | Average synchronization level |
| sync_ratio | [0, 1] | Fraction of time with R > 0.8 |
| phase_diff | [-π, π] | Phase lag between signals |

## Export Formats

The `export_results()` function creates:
- `sync_stats.csv` - Summary statistics
- `sync_timeseries.csv` - Time series data (R, phases, phase diff)
- `sync_dashboard.png` - Full dashboard visualization

## License

MIT License