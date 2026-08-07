# API Reference

Complete API reference for `synch_analysis` package.

## Public API (`synch_analysis`)

```python
from synch_analysis import (
    SignalPair,
    DataSource,
    ParquetDataSource,
    LorenzDataSource,
    SinusoidDataSource,
    CoupledOscillatorDataSource,
    BelousovZhabotinskyDataSource,
    SynchronizationAnalyzer,
    SynchronizationVisualizer,
    SynchronizationPipeline,
    compare_data_sources,
    export_results,
)
```

---

## Core Data Structures

### SignalPair

```python
class SignalPair:
    """Container for two signals to analyze for synchronization."""
    
    def __init__(
        self,
        signal_a: np.ndarray,
        signal_b: np.ndarray,
        time: Optional[np.ndarray] = None,
        name_a: str = "Signal A",
        name_b: str = "Signal B",
        sampling_rate: float = 1.0,
    ):
```

**Parameters:**
- `signal_a`, `signal_b`: numpy arrays of equal length
- `time`: Optional time array (auto-generated if None)
- `name_a`, `name_b`: Signal identifiers
- `sampling_rate`: Sampling frequency in Hz

**Properties:**
- `n_samples`: Number of samples in signals

---

### DataSource (Abstract Base Class)

```python
class DataSource(ABC):
    """Abstract base class for data sources."""
    
    @abstractmethod
    def load(self) -> SignalPair:
        """Load and return a SignalPair for analysis."""
    
    @abstractmethod
    def get_description(self) -> str:
        """Return a human-readable description of the data source."""
```

---

## Data Sources

### ParquetDataSource

```python
class ParquetDataSource(DataSource):
    """Load data from Parquet files (experimental/industrial data)."""
    
    def __init__(
        self,
        file_path: str,
        column_a: str,
        column_b: str,
        index_start: int = 0,
        index_end: Optional[int] = None,
        window: int = 60,
        lag: Optional[int] = None,
        sampling_rate: float = 1.0,
    ):
```

**Parameters:**
- `file_path`: Path to Parquet file
- `column_a`, `column_b`: Column names for signal A and B
- `index_start`, `index_end`: Row slice indices
- `window`: Rolling window for smoothing
- `lag`: Time lag to apply (positive = delay A relative to B)
- `sampling_rate`: Output sampling rate

**Processing:**
1. Load columns from Parquet
2. Apply rolling mean with `window`
3. Remove NaN from rolling
4. Apply lag if specified
5. Center signals (remove mean)
6. Symmetrize for Hilbert transform (mirror + concatenate)

**Example: T11/T12 Temperatures from datos_ind.pqt**
```python
from synch_analysis import ParquetDataSource, SynchronizationPipeline

# MW Inlet (T11) vs Outlet (T12) temperatures
parquet = ParquetDataSource(
    file_path="data/datos_ind.pqt",
    column_a="FormacionMWEntT11TempPV",
    column_b="FormacionMWSalT12TempPV",
    index_start=0,
    index_end=3600,  # 1 hour at 1 Hz
    window=10,
    lag=None,  # Test different lags manually
    sampling_rate=1.0
)

pipeline = SynchronizationPipeline(parquet).run()
pipeline.plot_dashboard()

# To find optimal lag:
for lag in range(-600, 601, 10):
    p = ParquetDataSource(
        file_path="data/datos_ind.pqt",
        column_a="FormacionMWEntT11TempPV",
        column_b="FormacionMWSalT12TempPV",
        index_start=0, index_end=3600,
        window=10, lag=lag, sampling_rate=1.0
    )
    stats = SynchronizationPipeline(p).run().get_stats()
    print(f"Lag {lag:4d}: Mean R = {stats['mean_R']:.4f}")
```

---

### LorenzDataSource

```python
class LorenzDataSource(DataSource):
    """Generate Lorenz attractor time series and its delayed version (sensor delay simulation)."""
    
    def __init__(
        self,
        a: float = 10.0,
        b: float = 28.0,
        c: float = 8.0 / 3.0,
        dt: float = 0.01,
        initial_values: Optional[List[float]] = None,
        iterations: int = 1000,
        variable: str = "x",
        delay_steps: int = 0,
        noise_std: float = 0.0,
        sampling_rate: float = 100.0,
    ):
```

**Parameters:**
- `a`, `b`, `c`: Lorenz system parameters (default: classic chaotic regime)
- `dt`: Time step for integration
- `initial_values`: Initial [x, y, z] (default: [0.01, 0, 0.3])
- `iterations`: Number of integration steps
- `variable`: Which variable to extract ("x", "y", or "z")
- `delay_steps`: Sensor delay in time steps (default: 0). Creates delayed version of signal A
- `noise_std`: Optional Gaussian noise std for delayed signal
- `sampling_rate`: Output sampling rate

---

### SinusoidDataSource

```python
class SinusoidDataSource(DataSource):
    """Generate sinusoidal signals with controllable phase/frequency."""
    
    def __init__(
        self,
        ph0_a: float = 0,
        ph0_b: float = 0,
        frq_a: float = 1,
        frq_b: float = 1,
        pers: int = 1,
        delay_a: float = 0,
        delay_b: float = 0,
        iterations: int = 1000,
        sampling_rate: float = 1.0,
    ):
```

**Parameters:**
- `ph0_a`, `ph0_b`: Initial phase offsets (radians)
- `frq_a`, `frq_b`: Frequency multipliers
- `pers`: Number of periods
- `delay_a`, `delay_b`: Time delays
- `iterations`: Number of samples
- `sampling_rate`: Output sampling rate

**Signal formula:**
```
sin((t - delay) + ph0) * cos(frq * (t - delay) + ph0)
```

---

### CoupledOscillatorDataSource

```python
class CoupledOscillatorDataSource(DataSource):
    """Generate synthetic coupled oscillators (Kuramoto model)."""
    
    def __init__(
        self,
        n_oscillators: int = 2,
        coupling_strength: float = 0.5,
        natural_freqs: Optional[np.ndarray] = None,
        dt: float = 0.01,
        duration: float = 100.0,
        noise_std: float = 0.0,
        sampling_rate: float = 100.0,
    ):
```

**Parameters:**
- `n_oscillators`: Number of oscillators (minimum 2)
- `coupling_strength`: Coupling parameter K
- `natural_freqs`: Array of natural frequencies (auto-generated if None)
- `dt`: Integration time step
- `duration`: Total simulation time
- `noise_std`: Gaussian noise standard deviation
- `sampling_rate`: Output sampling rate

**Model (Kuramoto):**
```
dφ_j/dt = ω_j + (K/N) Σ sin(φ_k - φ_j) + noise
```

---

### BelousovZhabotinskyDataSource

```python
class BelousovZhabotinskyDataSource(DataSource):
    """Generate Belousov-Zhabotinsky oscillator time series using the Oregonator model."""
    
    def __init__(
        self,
        f: float = 1.0,
        q: float = 0.05,
        eps: float = 0.02,
        dt: float = 0.01,
        initial_values: Optional[List[float]] = None,
        iterations: int = 10000,
        variable: str = "x",
        delay_steps: int = 100,
        noise_std: float = 0.05,
        sampling_rate: float = 100.0,
        transient: int = 2000,
    ):
```

**Parameters:**
- `f`: Stoichiometric parameter (default: 1.0, must be > 0.5 for oscillation)
- `q`: Small parameter (default: 0.05, typically 1e-4 to 0.1)
- `eps`: Time-scale separation parameter (default: 0.02, typically 0.01-0.1)
- `dt`: Integration time step (default: 0.01)
- `initial_values`: Initial [x, z] values (default: [0.1, 0.1])
- `iterations`: Number of integration steps (default: 10000)
- `variable`: Which variable to extract ("x" or "z") (default: "x")
- `delay_steps`: Sensor delay in time steps (default: 100). Creates delayed version of signal A
- `noise_std`: Gaussian noise standard deviation (default: 0.05)
- `sampling_rate`: Output sampling rate in Hz (default: 100.0)
- `transient`: Number of initial steps to discard (default: 2000)

**Model (Oregonator, 2-variable reduced form):**
```
ε(dx/dt) = x(1-x) - f·z·(x-q)/(x+q)
dz/dt = x - z
```

Uses scipy's LSODA stiff ODE solver.

**Reference:** Field, R.J., & Noyes, R.M. (1974). "Oscillations in Chemical Systems IV." J. Chem. Phys. 60, 1877-1884.

---

## Analysis Engine

### SynchronizationAnalyzer

```python
class SynchronizationAnalyzer:
    """Core analysis engine for Kuramoto order parameter computation."""
    
    def __init__(self, signal_pair: SignalPair):
```

**Methods:**

#### compute_hilbert_transform()
```python
def compute_hilbert_transform(self) -> Tuple[np.ndarray, np.ndarray]:
    """Compute analytic signals via Hilbert transform."""
    # Returns: (hilbert_a, hilbert_b)
```

Computes and stores:
- `hilbert_a`, `hilbert_b`: Analytic signals (complex)
- `amplitude_a`, `amplitude_b`: Instantaneous amplitudes
- `phase_a`, `phase_b`: Instantaneous phases (radians)

#### compute_order_parameter()
```python
def compute_order_parameter(self) -> np.ndarray:
    """Compute Kuramoto order parameter R(t) = |<e^(iφ)>|."""
    # Returns: order_parameter array
```

Computes and stores:
- `order_parameter`: R(t) ∈ [0, 1]
- `phase_diff`: Phase difference φ₁ - φ₂ (radians)

#### compute_sliding_order_parameter(window=50)
```python
def compute_sliding_order_parameter(self, window: int = 50) -> np.ndarray:
    """Compute sliding window order parameter (moving average)."""
```

#### get_summary_stats()
```python
def get_summary_stats(self) -> Dict[str, float]:
    """Get summary statistics."""
```

**Returns:**
- `mean_R`: Mean order parameter
- `std_R`: Standard deviation of R
- `max_R`: Maximum R
- `min_R`: Minimum R
- `mean_phase_diff`: Mean phase difference
- `std_phase_diff`: Std of phase difference
- `sync_ratio`: Fraction of time with R > 0.8

---

## Visualization

### SynchronizationVisualizer

```python
class SynchronizationVisualizer:
    """Visualization tools for synchronization analysis."""
    
    def __init__(self, analyzer: SynchronizationAnalyzer, figsize=(15, 10)):
```

**Methods:**

#### plot_signals(ax=None, n_samples=None)
Plot raw signals.

#### plot_hilbert_components(ax=None)
Plot Hilbert transform (real vs imaginary) for both signals.

#### plot_phases(ax=None)
Plot instantaneous phases over time.

#### plot_phase_portrait(ax=None)
Plot phases on unit circle.

#### plot_order_parameter(ax=None, sliding_window=None)
Plot Kuramoto order parameter R(t) over time.

#### plot_phase_difference(ax=None)
Plot phase difference φ₁ - φ₂ over time.

#### create_dashboard(sliding_window=50, n_signal_samples=500)
Create comprehensive 3×3 grid dashboard with all plots + statistics.

#### animate_phases(interval=50, trail_length=50)
Create animation of phase evolution on unit circle.

---

## Pipeline

### SynchronizationPipeline

```python
class SynchronizationPipeline:
    """End-to-end pipeline for synchronization analysis."""
    
    def __init__(self, data_source: DataSource):
```

**Methods:**

#### run()
```python
def run(self) -> "SynchronizationPipeline":
    """Execute the full pipeline."""
```

Returns self for chaining.

#### plot_dashboard(**kwargs)
```python
def plot_dashboard(self, **kwargs):
    """Create and show dashboard."""
```

#### animate(**kwargs)
```python
def animate(self, **kwargs):
    """Create phase animation."""
```

#### get_stats()
```python
def get_stats(self) -> Dict[str, float]:
    """Get analysis statistics."""
```

---

## Utilities

### compare_data_sources
```python
def compare_data_sources(
    sources: List[DataSource],
    labels: Optional[List[str]] = None
) -> pd.DataFrame:
    """Compare synchronization across multiple data sources."""
```

**Returns:** DataFrame with statistics for each source.

### export_results
```python
def export_results(pipeline: SynchronizationPipeline, output_dir: str = "results"):
    """Export analysis results to files."""
```

**Exports:**
- `sync_stats.csv`: Summary statistics
- `sync_timeseries.csv`: Time series (time, R, phase_diff, phase_a, phase_b)
- `sync_dashboard.png`: Dashboard figure

---

## Publication-Quality Figure Settings

All notebooks use publication-quality matplotlib settings for journal-ready figures:

```python
# Publication-quality figure settings
plt.rcParams.update({
    'figure.figsize': (14, 6),
    'font.size': 12,
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
    'lines.markersize': 4
})
```

**Key settings:**
- **White background**: `figure.facecolor` and `axes.facecolor` set to `'white'`
- **No grid**: `axes.grid` set to `False`
- **High DPI**: `figure.dpi` and `savefig.dpi` set to `300` for print quality
- **Tight layout**: `savefig.bbox` set to `'tight'` with minimal padding
- **Visible spines**: All axis spines visible for clear data boundaries
- **Publication-quality legends**: Semi-transparent frames with black edges