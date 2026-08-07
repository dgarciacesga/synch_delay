"""Data source implementations for different signal types."""

from typing import Optional, List
import numpy as np
import pandas as pd

from .core import SignalPair, DataSource


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
        self.file_path = file_path
        self.column_a = column_a
        self.column_b = column_b
        self.index_start = index_start
        self.index_end = index_end
        self.window = window
        self.lag = lag
        self.sampling_rate = sampling_rate

    def load(self) -> SignalPair:
        df = pd.read_parquet(self.file_path)

        if self.index_end is None:
            self.index_end = len(df)

        # Apply rolling mean to smooth
        series_a = (
            df[self.column_a].iloc[self.index_start : self.index_end].rolling(self.window).mean()
        )
        series_b = (
            df[self.column_b].iloc[self.index_start : self.index_end].rolling(self.window).mean()
        )

        # Remove NaN from rolling
        series_a = series_a.dropna()
        series_b = series_b.dropna()

        # Apply lag if specified
        if self.lag is not None:
            series_a = series_a.iloc[self.lag :].reset_index(drop=True)
            series_b = series_b.iloc[: -self.lag].reset_index(drop=True)

        # Center signals (remove mean)
        signal_a = (series_a - series_a.mean()).values
        signal_b = (series_b - series_b.mean()).values

        # Symmetrize for Hilbert transform
        signal_a = np.concatenate((signal_a[::-1], signal_a))
        signal_b = np.concatenate((signal_b[::-1], signal_b))

        return SignalPair(
            signal_a=signal_a,
            signal_b=signal_b,
            name_a=self.column_a,
            name_b=self.column_b,
            sampling_rate=self.sampling_rate,
        )

    def get_description(self) -> str:
        return f"Parquet: {self.file_path} [{self.column_a} vs {self.column_b}]"


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
        self.a, self.b, self.c = a, b, c
        self.dt = dt
        self.initial_values = initial_values or [0.01, 0, 0.3]
        self.iterations = iterations
        self.variable = variable
        self.delay_steps = delay_steps
        self.noise_std = noise_std
        self.sampling_rate = sampling_rate

    def _generate(self, initial_values: List[float]) -> np.ndarray:
        x, y, z = [initial_values[0]], [initial_values[1]], [initial_values[2]]
        for _ in range(self.iterations):
            dxdt = self.a * (y[-1] - x[-1])
            dydt = x[-1] * (self.b - z[-1]) - y[-1]
            dzdt = x[-1] * y[-1] - self.c * z[-1]
            x.append(x[-1] + self.dt * dxdt)
            y.append(y[-1] + self.dt * dydt)
            z.append(z[-1] + self.dt * dzdt)
        return np.array({"x": x, "y": y, "z": z}[self.variable])

    def load(self) -> SignalPair:
        signal_a = self._generate(self.initial_values)

        # Create delayed version of signal_a if delay specified
        if self.delay_steps > 0:
            signal_b = np.concatenate(
                [np.full(self.delay_steps, np.nan), signal_a[: -self.delay_steps]]
            )
            signal_b = pd.Series(signal_b).interpolate(limit_direction="both").values
        elif self.delay_steps < 0:
            signal_b = np.concatenate(
                [signal_a[-self.delay_steps :], np.full(-self.delay_steps, np.nan)]
            )
            signal_b = pd.Series(signal_b).interpolate(limit_direction="both").values
        else:
            signal_b = signal_a.copy()

        # Add optional noise to delayed signal
        if self.noise_std > 0:
            signal_b += np.random.normal(0, self.noise_std, len(signal_b))

        # Center signals
        signal_a = signal_a - np.mean(signal_a)
        signal_b = signal_b - np.mean(signal_b)

        if self.delay_steps != 0:
            name_b = f"Lorenz {self.variable} (delayed by {self.delay_steps} steps)"
        else:
            name_b = f"Lorenz {self.variable} (IC2)"

        return SignalPair(
            signal_a=signal_a,
            signal_b=signal_b,
            name_a=f"Lorenz {self.variable} (source)",
            name_b=name_b,
            sampling_rate=self.sampling_rate,
        )

    def get_description(self) -> str:
        return f"Lorenz attractor: a={self.a}, b={self.b}, c={self.c:.3f}, var={self.variable}, delay={self.delay_steps} steps, noise={self.noise_std}"


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
        self.ph0_a, self.ph0_b = ph0_a, ph0_b
        self.frq_a, self.frq_b = frq_a, frq_b
        self.pers = pers
        self.delay_a, self.delay_b = delay_a, delay_b
        self.iterations = iterations
        self.sampling_rate = sampling_rate

    def _generate(self, ph0: float, frq: float, delay: float) -> np.ndarray:
        t = np.linspace(0, 2 * np.pi * self.pers, self.iterations)
        return np.sin((t - delay) + ph0) * np.cos(frq * (t - delay) + ph0)

    def load(self) -> SignalPair:
        signal_a = self._generate(self.ph0_a, self.frq_a, self.delay_a)
        signal_b = self._generate(self.ph0_b, self.frq_b, self.delay_b)

        return SignalPair(
            signal_a=signal_a,
            signal_b=signal_b,
            name_a=f"Sin phi0={self.ph0_a}, f={self.frq_a}, d={self.delay_a}",
            name_b=f"Sin phi0={self.ph0_b}, f={self.frq_b}, d={self.delay_b}",
            sampling_rate=self.sampling_rate,
        )

    def get_description(self) -> str:
        return f"Sinusoids: phi0_1={self.ph0_a}, f1={self.frq_a}, d1={self.delay_a} | phi0_2={self.ph0_b}, f2={self.frq_b}, d2={self.delay_b}"


class BelousovZhabotinskyDataSource(DataSource):
    """Generate Belousov-Zhabotinsky oscillator time series using the Oregonator model.

    The Oregonator is the simplest realistic model of the BZ reaction chemical dynamics.
    Uses the reduced (2-variable) form via steady-state approximation for y:
        ε(dx/dt) = qy - xy + x(1 - x)
        ε'(dy/dt) = -qy - xy + fz
        dz/dt = x - z
    Reduced form (y steady-state):
        ε(dx/dt) = x(1-x) - f*z*(x-q)/(x+q)
        dz/dt = x - z

    Parameters for oscillatory regime:
        f: stoichiometric parameter (typically 0.5-3, must be > 0.5 for oscillation)
        q: small parameter (typically 1e-4 to 0.1)
        eps: time-scale separation parameter (typically 0.01-0.1)

    Uses scipy's LSODA solver for stiff ODE integration.

    Reference: Field, R.J., & Noyes, R.M. (1974). "Oscillations in Chemical Systems IV."
                J. Chem. Phys. 60, 1877-1884.
               Epstein, R.J., & Pojman, A.P. (1998). "An Introduction to Nonlinear
               Chemical Dynamics." Oxford University Press.
    """

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
        self.f = f
        self.q = q
        self.eps = eps
        self.dt = dt
        self.initial_values = initial_values or [0.1, 0.1]
        self.iterations = iterations
        self.variable = variable
        self.delay_steps = delay_steps
        self.noise_std = noise_std
        self.sampling_rate = sampling_rate
        self.transient = transient

    def _generate(self, initial_values: List[float]) -> np.ndarray:
        """Generate Oregonator time series using scipy's LSODA stiff solver."""
        from scipy.integrate import solve_ivp

        t_end = self.iterations * self.dt

        def oregonator(t, y):
            x, z = y
            dx = (1.0 / self.eps) * (x * (1 - x) - self.f * z * (x - self.q) / (x + self.q))
            dz = x - z
            return [dx, dz]

        sol = solve_ivp(
            oregonator,
            [0, t_end],
            initial_values,
            method="LSODA",
            dense_output=True,
        )

        t_grid = np.arange(0, t_end, self.dt)
        y = sol.sol(t_grid)
        signals = {"x": y[0], "z": y[1]}
        signal = signals[self.variable]

        # Remove transient
        if self.transient > 0 and len(signal) > self.transient:
            signal = signal[self.transient :]

        return signal

    def load(self) -> SignalPair:
        signal_a = self._generate(self.initial_values)

        if self.delay_steps > 0:
            signal_b = np.concatenate(
                [np.full(self.delay_steps, np.nan), signal_a[: -self.delay_steps]]
            )
            signal_b = pd.Series(signal_b).interpolate(limit_direction="both").values
        elif self.delay_steps < 0:
            signal_b = np.concatenate(
                [signal_a[-self.delay_steps :], np.full(-self.delay_steps, np.nan)]
            )
            signal_b = pd.Series(signal_b).interpolate(limit_direction="both").values
        else:
            signal_b = signal_a.copy()

        # Add noise to BOTH signals
        if self.noise_std > 0:
            rng = np.random.default_rng(42)
            signal_a = signal_a + rng.normal(0, self.noise_std, len(signal_a))
            signal_b = signal_b + rng.normal(0, self.noise_std, len(signal_b))

        signal_a = signal_a - np.mean(signal_a)
        signal_b = signal_b - np.mean(signal_b)

        if self.delay_steps != 0:
            name_b = f"BZ {self.variable} (delayed by {self.delay_steps} steps)"
        else:
            name_b = f"BZ {self.variable} (run 2)"

        return SignalPair(
            signal_a=signal_a,
            signal_b=signal_b,
            name_a=f"BZ {self.variable} (source)",
            name_b=name_b,
            sampling_rate=self.sampling_rate,
        )

    def get_description(self) -> str:
        return f"Belousov-Zhabotinsky (Oregonator): f={self.f}, q={self.q}, eps={self.eps}, var={self.variable}, delay={self.delay_steps} steps, noise={self.noise_std}"


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
        self.n_oscillators = n_oscillators
        self.coupling_strength = coupling_strength
        if natural_freqs is None:
            self.natural_freqs = np.random.normal(1.0, 0.1, n_oscillators)
        else:
            self.natural_freqs = np.array(natural_freqs)
        self.dt = dt
        self.duration = duration
        self.noise_std = noise_std
        self.sampling_rate = sampling_rate

    def load(self) -> SignalPair:
        n_steps = int(self.duration / self.dt)
        phases = np.random.uniform(0, 2 * np.pi, self.n_oscillators)

        # Store phase trajectories
        phase_history = np.zeros((n_steps, self.n_oscillators))

        for i in range(n_steps):
            phase_history[i] = phases
            # Kuramoto model
            for j in range(self.n_oscillators):
                coupling = sum(
                    np.sin(phases[k] - phases[j]) for k in range(self.n_oscillators) if j != k
                )
                dphase = self.natural_freqs[j] + self.coupling_strength * coupling / (
                    self.n_oscillators - 1
                )
                if self.noise_std > 0:
                    dphase += np.random.normal(0, self.noise_std)
                phases[j] += dphase * self.dt

        # Convert to signals (cosine of phase)
        signal_a = np.cos(phase_history[:, 0])
        signal_b = np.cos(phase_history[:, 1])

        return SignalPair(
            signal_a=signal_a,
            signal_b=signal_b,
            name_a=f"Oscillator 1 (w={self.natural_freqs[0]:.2f})",
            name_b=f"Oscillator 2 (w={self.natural_freqs[1]:.2f})",
            sampling_rate=self.sampling_rate,
        )

    def get_description(self) -> str:
        return f"Coupled oscillators: K={self.coupling_strength}, w={self.natural_freqs}"
