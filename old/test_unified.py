import numpy as np
from scipy.signal import hilbert
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Optional
import warnings
warnings.filterwarnings('ignore')

@dataclass
class SignalPair:
    signal_a: np.ndarray
    signal_b: np.ndarray
    time: Optional[np.ndarray] = None
    name_a: str = 'Signal A'
    name_b: str = 'Signal B'
    sampling_rate: float = 1.0
    def __post_init__(self):
        if self.time is None:
            self.time = np.arange(len(self.signal_a)) / self.sampling_rate
        assert len(self.signal_a) == len(self.signal_b)
    @property
    def n_samples(self): return len(self.signal_a)

class DataSource(ABC):
    @abstractmethod
    def load(self) -> SignalPair: pass
    @abstractmethod
    def get_description(self) -> str: pass

class LorenzDataSource(DataSource):
    def __init__(self, a=10.0, b=28.0, c=8.0/3.0, dt=0.01, 
                 initial_values_1=None, initial_values_2=None, 
                 iterations=1000, variable='x', sampling_rate=100.0):
        self.a, self.b, self.c = a, b, c
        self.dt = dt
        self.initial_values_1 = initial_values_1 or [0.01, 0, 0.3]
        self.initial_values_2 = initial_values_2 or [0.2, 0.1, 0.4]
        self.iterations = iterations
        self.variable = variable
        self.sampling_rate = sampling_rate
    def _generate(self, iv):
        x, y, z = [iv[0]], [iv[1]], [iv[2]]
        for _ in range(self.iterations):
            dxdt = self.a * (y[-1] - x[-1])
            dydt = x[-1] * (self.b - z[-1]) - y[-1]
            dzdt = x[-1] * y[-1] - self.c * z[-1]
            x.append(x[-1] + self.dt * dxdt)
            y.append(y[-1] + self.dt * dydt)
            z.append(z[-1] + self.dt * dzdt)
        return np.array({'x': x, 'y': y, 'z': z}[self.variable])
    def load(self):
        s1 = self._generate(self.initial_values_1)
        s2 = self._generate(self.initial_values_2)
        return SignalPair(s1, s2, name_a=f'Lorenz {self.variable} (IC1)', name_b=f'Lorenz {self.variable} (IC2)', sampling_rate=self.sampling_rate)
    def get_description(self): return f'Lorenz: a={self.a}, b={self.b}, c={self.c:.3f}, var={self.variable}'

class SinusoidDataSource(DataSource):
    def __init__(self, ph0_a=0, ph0_b=0, frq_a=1, frq_b=1, pers=1, delay_a=0, delay_b=0, iterations=1000, sampling_rate=1.0):
        self.ph0_a, self.ph0_b = ph0_a, ph0_b
        self.frq_a, self.frq_b = frq_a, frq_b
        self.pers = pers
        self.delay_a, self.delay_b = delay_a, delay_b
        self.iterations = iterations
        self.sampling_rate = sampling_rate
    def _gen(self, ph0, frq, delay):
        t = np.linspace(0, 2*np.pi*self.pers, self.iterations)
        return np.sin((t - delay) + ph0) * np.cos(frq * (t - delay) + ph0)
    def load(self):
        s1 = self._gen(self.ph0_a, self.frq_a, self.delay_a)
        s2 = self._gen(self.ph0_b, self.frq_b, self.delay_b)
        return SignalPair(s1, s2, name_a='Sin ph0={}, frq={}, delay={}'.format(self.ph0_a, self.frq_a, self.delay_a), name_b='Sin ph0={}, frq={}, delay={}'.format(self.ph0_b, self.frq_b, self.delay_b), sampling_rate=self.sampling_rate)
    def get_description(self): return 'Sinusoids: ph0_1={}, f1={}, d1={} | ph0_2={}, f2={}, d2={}'.format(self.ph0_a, self.frq_a, self.delay_a, self.ph0_b, self.frq_b, self.delay_b)

class CoupledOscillatorDataSource(DataSource):
    def __init__(self, n_oscillators=2, coupling_strength=0.5, natural_freqs=None, dt=0.01, duration=100.0, noise_std=0.0, sampling_rate=100.0):
        self.n_oscillators = n_oscillators
        self.coupling_strength = coupling_strength
        if natural_freqs is None:
            self.natural_freqs = np.random.normal(1.0, 0.1, n_oscillators)
        else:
            self.natural_freqs = natural_freqs
        self.dt = dt
        self.duration = duration
        self.noise_std = noise_std
        self.sampling_rate = sampling_rate
    def load(self):
        n_steps = int(self.duration / self.dt)
        phases = np.random.uniform(0, 2*np.pi, self.n_oscillators)
        phase_history = np.zeros((n_steps, self.n_oscillators))
        for i in range(n_steps):
            phase_history[i] = phases
            for j in range(self.n_oscillators):
                coupling = sum(np.sin(phases[k] - phases[j]) for k in range(self.n_oscillators) if j != k)
                dphase = self.natural_freqs[j] + self.coupling_strength * coupling / (self.n_oscillators - 1)
                if self.noise_std > 0: dphase += np.random.normal(0, self.noise_std)
                phases[j] += dphase * self.dt
        s1 = np.cos(phase_history[:, 0])
        s2 = np.cos(phase_history[:, 1])
        return SignalPair(s1, s2, name_a='Osc 1 (w={:.2f})'.format(self.natural_freqs[0]), name_b='Osc 2 (w={:.2f})'.format(self.natural_freqs[1]), sampling_rate=self.sampling_rate)
    def get_description(self): return 'Coupled oscillators: K={}, w={}'.format(self.coupling_strength, self.natural_freqs)

# Test
print("Testing Lorenz...")
lorenz = LorenzDataSource(iterations=500)
pair = lorenz.load()
print(f"  {pair.name_a} vs {pair.name_b}, {pair.n_samples} samples")

print("Testing Sinusoids...")
sin = SinusoidDataSource(frq_a=2, frq_b=2, delay_a=0, delay_b=3, iterations=500)
pair = sin.load()
print("  {} vs {}, {} samples".format(pair.name_a, pair.name_b, pair.n_samples))

print("Testing Coupled Oscillators...")
coupled = CoupledOscillatorDataSource(coupling_strength=0.8, natural_freqs=np.array([1.0, 1.05]), duration=20.0)
pair = coupled.load()
print("  {} vs {}, {} samples".format(pair.name_a, pair.name_b, pair.n_samples))

print("\nAll data sources work!")