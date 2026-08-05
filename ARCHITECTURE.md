# Architecture Documentation

Technical architecture and design decisions for `synch_analysis`.

---

## System Overview

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                            synch_analysis v1.0.0                             │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  ┌──────────────┐    ┌──────────────┐    ┌──────────────────────────────┐  │
│  │ Data Sources │───▶│  Core Types  │───▶│     Analysis Engine          │  │
│  │              │    │              │    │                              │  │
│  │ • Parquet    │    │ • SignalPair │    │ • Hilbert Transform          │  │
│  │ • Lorenz     │    │ • DataSource │    │ • Kuramoto Order Parameter   │  │
│  │ • Sinusoid   │    │   (ABC)      │    │ • Phase Difference           │  │
│  │ • Coupled    │    └──────────────┘    │ • Sliding Window             │  │
│  └──────────────┘                         │ • Summary Statistics         │  │
│                                           └──────────────┬───────────────┘  │
│                                                          │                  │
│  ┌──────────────┐    ┌──────────────┐    ┌──────────────┴──────────────┐  │
│  │   Pipeline   │◀───│  Visualizer  │◀───│    SynchronizationAnalyzer  │  │
│  │              │    │              │    │                              │  │
│  │ • run()      │    │ • Dashboard  │    │  (Stateful analysis object)  │  │
│  │ • compare()  │    │ • Animations │    └──────────────────────────────┘  │
│  │ • export()   │    │ • Phase plots│                                     │  │
│  └──────────────┘    └──────────────┘                                     │  │
│         │                    │                                            │  │
│         └────────────────────┴────────────────────────────────────────────┘  │
│                                      │                                        │
│                    ┌─────────────────┼─────────────────┐                     │
│                    ▼                 ▼                 ▼                     │
│             ┌──────────┐      ┌──────────┐      ┌──────────┐                │
│             │   CSV    │      │   PNG    │      │   GIF    │                │
│             │  Stats   │      │ Dashboard│      │ Animation│                │
│             │  Series  │      │          │      │          │                │
│             └──────────┘      └──────────┘      └──────────┘                │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## Module Dependencies

```
synch_analysis/
├── core.py          # ← No internal dependencies (base)
├── sources.py       # ← core.py
├── analyzer.py      # ← core.py, scipy.signal, numpy, pandas
├── visualizer.py    # ← analyzer.py, core.py, matplotlib
├── pipeline.py      # ← sources.py, analyzer.py, visualizer.py
└── cli.py           # ← pipeline.py, sources.py
```

**Dependency Graph:**
```
core.py (base)
    │
    ├── sources.py (data sources)
    │
    ├── analyzer.py (computations)
    │       │
    │       └── visualizer.py (plots)
    │             │
    │             └── pipeline.py (orchestration)
    │                   │
    │                   └── cli.py (command line)
```

---

## Core Data Structures

### SignalPair (`core.py:9-27`)

```python
@dataclass
class SignalPair:
    signal_a: np.ndarray
    signal_b: np.ndarray
    time: Optional[np.ndarray] = None
    name_a: str = "Signal A"
    name_b: str = "Signal B"
    sampling_rate: float = 1.0
```

**Purpose:** Immutable container for signal pair with metadata.

**Key behaviors:**
- Auto-generates `time` array if not provided
- Validates equal length in `__post_init__`
- Provides `n_samples` property

**Design rationale:**
- Dataclass for immutability and clarity
- Explicit sampling rate enables correct time axis
- Names used throughout visualization for labeling

---

### DataSource (`core.py:30-41`)

```python
class DataSource(ABC):
    @abstractmethod
    def load(self) -> SignalPair: ...
    @abstractmethod
    def get_description(self) -> str: ...
```

**Purpose:** Strategy pattern for data loading.

**Contract:**
- `load()`: Must return fully-formed `SignalPair`
- `get_description()`: Human-readable identifier for logs/exports

---

## Data Source Implementations (`sources.py`)

### ParquetDataSource

```python
def load(self) -> SignalPair:
    df = pd.read_parquet(self.file_path)
    # 1. Slice rows
    # 2. Rolling mean (window)
    # 3. Drop NaN
    # 4. Apply lag
    # 5. Center (remove mean)
    # 6. Symmetrize for Hilbert
    signal_a = np.concatenate((signal_a[::-1], signal_a))
```

**Processing pipeline:**
1. **Slice**: `index_start:index_end`
2. **Smooth**: `rolling(window).mean()`
3. **Clean**: `dropna()`
4. **Lag**: Shift A forward, B backward
5. **Center**: Subtract mean
6. **Symmetrize**: Mirror + concatenate

**Symmetrization rationale:** Reduces Hilbert transform edge effects by making signal symmetric at boundaries.

---

### LorenzDataSource

```python
def _generate(self, initial_values: List[float]) -> np.ndarray:
    x, y, z = initial_values
    for _ in range(self.iterations):
        dxdt = self.a * (y - x)
        dydt = x * (self.b - z) - y
        dzdt = x * y - self.c * z
        x += self.dt * dxdt
        y += self.dt * dydt
        z += self.dt * dzdt
    return np.array(variable_dict[self.variable])
```

**Integration:** Simple Euler method (sufficient for analysis purposes).

**Variables:** Selectable "x", "y", or "z" component.

---

### SinusoidDataSource

```python
def _generate(self, ph0: float, frq: float, delay: float) -> np.ndarray:
    t = np.linspace(0, 2 * np.pi * self.pers, self.iterations)
    return np.sin((t - delay) + ph0) * np.cos(frq * (t - delay) + ph0)
```

**Signal:** Amplitude-modulated sinusoid with controllable phase, frequency, delay.

---

### CoupledOscillatorDataSource

```python
for i in range(n_steps):
    phase_history[i] = phases
    for j in range(self.n_oscillators):
        coupling = sum(np.sin(phases[k] - phases[j]) 
                      for k in range(self.n_oscillators) if j != k)
        dphase = self.natural_freqs[j] + self.coupling_strength * coupling / (N - 1)
        if self.noise_std > 0:
            dphase += np.random.normal(0, self.noise_std)
        phases[j] += dphase * self.dt

signal_a = np.cos(phase_history[:, 0])
signal_b = np.cos(phase_history[:, 1])
```

**Model:** Kuramoto model with N oscillators, all-to-all coupling.

**Output:** Cosine of phase for first two oscillators.

---

## Analysis Engine (`analyzer.py`)

### SynchronizationAnalyzer

**Stateful design:** Stores all intermediate results as instance attributes.

```python
class SynchronizationAnalyzer:
    def __init__(self, signal_pair: SignalPair):
        self.signal_pair = signal_pair
        self.hilbert_a = self.hilbert_b = None
        self.phase_a = self.phase_b = None
        self.amplitude_a = self.amplitude_b = None
        self.order_parameter = None
        self.phase_diff = None
```

**Computation flow:**

```
1. compute_hilbert_transform()
   ├─ hilbert(signal_a) → hilbert_a (complex)
   ├─ hilbert(signal_b) → hilbert_b (complex)
   ├─ amplitude = |hilbert|
   └─ phase = angle(hilbert)

2. compute_order_parameter()
   ├─ z_a = exp(i * phase_a)
   ├─ z_b = exp(i * phase_b)
   ├─ order_parameter = |(z_a + z_b) / 2|
   └─ phase_diff = angle(z_a / z_b)
```

**Mathematical details:**

For N=2 oscillators:
```
R(t) = |(e^(iφ₁) + e^(iφ₂)) / 2|
     = |cos((φ₁ - φ₂)/2)|
```

Phase difference:
```
Δφ(t) = φ₁(t) - φ₂(t)  (wrapped to [-π, π])
```

**Sliding window:** Uses `pandas.Series.rolling().mean()` for efficiency.

---

## Visualization (`visualizer.py`)

### SynchronizationVisualizer

**Design:** Object-oriented matplotlib wrapper.

```python
class SynchronizationVisualizer:
    def __init__(self, analyzer: SynchronizationAnalyzer, figsize=(15, 10)):
        self.analyzer = analyzer
        self.figsize = figsize
```

**Plot methods:** Each returns `Axes` for composability.

| Method | Purpose | Key Elements |
|--------|---------|--------------|
| `plot_signals` | Raw time series | Time vs amplitude |
| `plot_hilbert_components` | Analytic signal | Real vs Imaginary |
| `plot_phases` | Instantaneous phase | Time vs phase |
| `plot_phase_portrait` | Unit circle | cos(φ) vs sin(φ) |
| `plot_order_parameter` | R(t) | Time vs R, threshold line |
| `plot_phase_difference` | Δφ(t) | Time vs Δφ, ±π lines |
| `create_dashboard` | Full 3×3 grid | All plots + stats |
| `animate_phases` | Animation | Moving points on circle |

**Dashboard layout (3×3 GridSpec):**

```
┌──────────┬──────────┬──────────┐
│ Signals  │ Hilbert A│ Hilbert B│  ← Row 0
├──────────┼──────────┼──────────┤
│ Phases   │Portrait  │ R(t)     │  ← Row 1
├──────────┼──────────┼──────────┤
│ Δφ(t)    │   Stats  │   Stats  │  ← Row 2 (spans 2 cols)
└──────────┴──────────┴──────────┘
```

**Figure settings:**
All notebooks use publication-quality settings:
- White background (`figure.facecolor` and `axes.facecolor`)
- No grid lines (`axes.grid: False`)
- High DPI (300) for print quality
- Tight bounding box for minimal whitespace
- Visible axis spines for clear data boundaries

---

## Pipeline (`pipeline.py`)

### SynchronizationPipeline

**Purpose:** Facade pattern - simplifies common workflow.

```python
class SynchronizationPipeline:
    def __init__(self, data_source: DataSource):
        self.data_source = data_source
        self.signal_pair = None
        self.analyzer = None
        self.visualizer = None
    
    def run(self) -> "SynchronizationPipeline":
        # 1. Load data
        self.signal_pair = self.data_source.load()
        # 2. Create analyzer
        self.analyzer = SynchronizationAnalyzer(self.signal_pair)
        # 3. Create visualizer
        self.visualizer = SynchronizationVisualizer(self.analyzer)
        # 4. Compute
        self.analyzer.compute_hilbert_transform()
        self.analyzer.compute_order_parameter()
        # 5. Print summary
        return self
```

**Fluent interface:** Returns `self` for chaining.

---

### compare_data_sources

```python
def compare_data_sources(sources: List[DataSource], 
                         labels: Optional[List[str]] = None) -> pd.DataFrame:
    results = []
    for i, source in enumerate(sources):
        label = labels[i] if labels else source.get_description()
        pipeline = SynchronizationPipeline(source).run()
        stats = pipeline.get_stats()
        stats["source"] = label
        results.append(stats)
    return pd.DataFrame(results)
```

**Output columns:** `source, mean_R, std_R, max_R, min_R, mean_phase_diff, std_phase_diff, sync_ratio`

---

### export_results

```python
def export_results(pipeline: SynchronizationPipeline, output_dir: str = "results"):
    Path(output_dir).mkdir(exist_ok=True)
    
    # 1. Stats CSV
    pd.Series(pipeline.get_stats()).to_csv(f"{output_dir}/sync_stats.csv")
    
    # 2. Time series CSV
    df = pd.DataFrame({
        "time": pipeline.analyzer.signal_pair.time[:len(R)],
        "R": R,
        "phase_diff": phase_diff,
        "phase_a": phase_a,
        "phase_b": phase_b,
    })
    df.to_csv(f"{output_dir}/sync_timeseries.csv", index=False)
    
    # 3. Dashboard PNG
    fig = pipeline.plot_dashboard()
    fig.savefig(f"{output_dir}/sync_dashboard.png", dpi=150)
    plt.close(fig)
```

---

## CLI (`cli.py`)

### Architecture

```
main()
  ├─ create_source(args) → DataSource
  ├─ SynchronizationPipeline(source).run()
  ├─ pipeline.get_stats() → print
  └─ export_results(pipeline, args.output)
```

**Argument structure:**
- Positional: `type` (lorenz|sinusoid|coupled|parquet)
- Common: `--output`, `--dashboard`, `--stats`, `--format`
- Type-specific: Grouped by source type

**Entry point:** `synch-analysis` (defined in `pyproject.toml`)

---

## Configuration

### pyproject.toml

```toml
[project]
name = "synch_analysis"
version = "1.0.0"
dependencies = [
    "numpy>=1.21.0",
    "pandas>=1.3.0",
    "scipy>=1.7.0",
    "matplotlib>=3.4.0",
    "seaborn>=0.11.0",
]

[project.optional-dependencies]
dev = ["pytest>=7.0", "black>=22.0", "flake8>=4.0", "mypy>=0.950", "jupyter>=1.0"]

[tool.setuptools.packages.find]
where = ["src"]
include = ["synch_analysis*"]

[tool.black]
line-length = 100
target-version = ["py38"]

[tool.mypy]
python_version = "3.8"
warn_return_any = true
disallow_untyped_defs = true
```

---

## Type Hints

**Coverage:** All public APIs have type hints.

**Standards:**
- `numpy.typing.NDArray` for arrays (where version permits)
- `Optional[]` for nullable
- `Tuple[]`, `List[]`, `Dict[]` for collections
- `Protocol` not used (ABC preferred for runtime checking)

---

## Testing Strategy

### Unit Tests (recommended structure)

```
tests/
├── test_core.py          # SignalPair, DataSource ABC
├── test_sources.py       # Each DataSource implementation
├── test_analyzer.py      # Hilbert, order parameter, stats
├── test_visualizer.py    # Plot creation (mock matplotlib)
├── test_pipeline.py      # Pipeline orchestration
└── test_cli.py           # CLI argument parsing
```

### Key Test Cases

| Component | Tests |
|-----------|-------|
| SignalPair | Equal length validation, time generation |
| ParquetDataSource | Rolling window, lag, symmetrization |
| LorenzDataSource | Parameter variations, variable selection |
| Analyzer | Hilbert output shape, R ∈ [0,1], phase diff wrapping |
| Pipeline | run() chain, export file creation |
| CLI | All subcommands, help output |

---

## Performance Considerations

### Computational Complexity

| Operation | Complexity | Notes |
|-----------|------------|-------|
| Hilbert transform | O(N log N) | FFT-based (scipy) |
| Order parameter | O(N) | Vectorized numpy |
| Sliding window | O(N × W) | Pandas rolling |
| Visualization | O(N) | Matplotlib rendering |

### Memory Usage

- **SignalPair:** 2 × N × 8 bytes (float64)
- **Hilbert:** 2 × N × 16 bytes (complex128)
- **Phases:** 2 × N × 8 bytes
- **Order parameter:** N × 8 bytes
- **Total:** ~80 bytes per sample

**Typical:** 10,000 samples ≈ 0.8 MB

---

## Extensibility Points

### Adding New Data Source

1. Create class in `sources.py` inheriting `DataSource`
2. Implement `load()` → `SignalPair`
3. Implement `get_description()` → `str`
4. Add to `__init__.py` exports
5. Add CLI support in `cli.py:create_source()`

### Adding New Analysis Metric

1. Add method to `SynchronizationAnalyzer`
2. Store result as instance attribute
3. Add to `get_summary_stats()`
4. Add visualization in `SynchronizationVisualizer`
5. Include in `export_results()`

### Adding New Visualization

1. Add method to `SynchronizationVisualizer`
2. Accept optional `ax` parameter
3. Return `Axes` for composability
4. Add to `create_dashboard()` if appropriate

---

## Error Handling

### Current Approach

- **DataSource.load()**: May raise `FileNotFoundError`, `KeyError`, `ValueError`
- **Analyzer**: Validates state before computation
- **Pipeline.run()**: Catches and prints errors with context
- **CLI**: Top-level try/except with exit code 1

### Recommended Improvements

```python
# Custom exceptions (not yet implemented)
class SynchAnalysisError(Exception): pass
class DataLoadError(SynchAnalysisError): pass
class AnalysisError(SynchAnalysisError): pass
class VisualizationError(SynchAnalysisError): pass
```

---

## Future Architecture Considerations

### Potential Extensions

1. **Multi-signal support:** Extend `SignalPair` → `SignalGroup` (N signals)
2. **Streaming analysis:** Incremental Hilbert transform for real-time
3. **GPU acceleration:** CuPy for large-scale Hilbert transforms
4. **Parallel comparison:** `ProcessPoolExecutor` in `compare_data_sources`
5. **Configuration files:** YAML/JSON for reproducible experiments
6. **Database backend:** SQLAlchemy for result storage
7. **Web API:** FastAPI wrapper for remote analysis

### Migration Path for N-Signal Analysis

```python
# Current (N=2)
class SignalPair:
    signal_a: np.ndarray
    signal_b: np.ndarray

# Future (N≥2)
class SignalGroup:
    signals: List[np.ndarray]
    names: List[str]
    time: Optional[np.ndarray]
    sampling_rate: float
    
# Analyzer generalization
def compute_order_parameter(self) -> np.ndarray:
    # R(t) = |(1/N) Σ e^(iφ_k)|
    phase_matrix = np.array([self.phase_k for k in range(N)])
    z_matrix = np.exp(1j * phase_matrix)
    self.order_parameter = np.abs(z_matrix.mean(axis=0))
```