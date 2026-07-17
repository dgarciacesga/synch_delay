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

---

### LorenzDataSource

```python
class LorenzDataSource(DataSource):
    """Generate Lorenz attractor time series."""
    
    def __init__(
        self,
        a: float = 10.0,
        b: float = 28.0,
        c: float = 8.0 / 3.0,
        dt: float = 0.01,
        initial_values_1: Optional[List[float]] = None,
        initial_values_2: Optional[List[float]] = None,
        iterations: int = 1000,
        variable: str = "x",
        sampling_rate: float = 100.0,
    ):
```

**Parameters:**
- `a`, `b`, `c`: Lorenz system parameters (default: classic chaotic regime)
- `dt`: Time step for integration
- `initial_values_1`, `initial_values_2`: Initial [x, y, z] for two trajectories
- `iterations`: Number of integration steps
- `variable`: Which variable to extract ("x", "y", or "z")
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