"""Command-line interface for synchronization analysis."""

import argparse
import sys
import json
from pathlib import Path

import numpy as np

from . import (
    LorenzDataSource,
    SinusoidDataSource,
    CoupledOscillatorDataSource,
    BelousovZhabotinskyDataSource,
    ParquetDataSource,
    SynchronizationPipeline,
    export_results,
)


def create_source(args):
    """Create data source from command line arguments."""
    if args.type == "lorenz":
        return LorenzDataSource(
            a=args.a,
            b=args.b,
            c=args.c,
            dt=args.dt,
            initial_values=[args.x, args.y, args.z],
            iterations=args.iterations,
            variable=args.variable,
            sampling_rate=args.sampling_rate,
            delay_steps=args.delay_steps,
            noise_std=args.noise,
        )
    elif args.type == "sinusoid":
        return SinusoidDataSource(
            ph0_a=args.ph0_a,
            ph0_b=args.ph0_b,
            frq_a=args.frq_a,
            frq_b=args.frq_b,
            pers=args.pers,
            delay_a=args.delay_a,
            delay_b=args.delay_b,
            iterations=args.iterations,
            sampling_rate=args.sampling_rate,
        )
    elif args.type == "coupled":
        return CoupledOscillatorDataSource(
            n_oscillators=len(args.freqs),
            coupling_strength=args.coupling,
            natural_freqs=np.array(args.freqs),
            dt=args.dt,
            duration=args.duration,
            noise_std=args.noise,
            sampling_rate=args.sampling_rate,
        )
    elif args.type == "parquet":
        return ParquetDataSource(
            file_path=args.file,
            column_a=args.col_a,
            column_b=args.col_b,
            index_start=args.start,
            index_end=args.end,
            window=args.window,
            lag=args.lag,
            sampling_rate=args.sampling_rate,
        )
    elif args.type == "bz":
        return BelousovZhabotinskyDataSource(
            f=args.bz_f,
            q=args.bz_q,
            eps=args.bz_eps,
            dt=args.bz_dt,
            initial_values=[args.bz_x0, args.bz_z0],
            iterations=args.bz_iterations,
            variable=args.bz_variable,
            delay_steps=args.bz_delay_steps,
            noise_std=args.bz_noise,
            sampling_rate=args.sampling_rate,
            transient=args.bz_transient,
        )
    else:
        raise ValueError(f"Unknown source type: {args.type}")


def main():
    parser = argparse.ArgumentParser(
        description="Synchronization Analysis using Kuramoto Order Parameter",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Lorenz attractor with sensor delay
  synch-analysis lorenz --iterations 5000 --delay-steps 150 --noise 0.05 --output results/
  
  # Lorenz attractor (single signal, no delay)
  synch-analysis lorenz --iterations 1000 --output results/
  
  # Sinusoidal signals with phase delay
  synch-analysis sinusoid --delay-b 3 --output results/
  
  # Coupled oscillators
  synch-analysis coupled --coupling 0.8 --freqs 1.0 1.05 --output results/
  
  # Parquet data
  synch-analysis parquet --file data.pqt --col-a Temp1 --col-b Temp2 --output results/
  
  # Belousov-Zhabotinsky (Oregonator model)
  synch-analysis bz --iterations 10000 --delay-steps 100 --noise 0.05 --output results/
  """,
    )

    subparsers = parser.add_subparsers(dest="type", required=True, help="Data source type")

    # Common arguments for all subparsers
    common_parser = argparse.ArgumentParser(add_help=False)
    common_parser.add_argument("--output", "-o", default="results", help="Output directory")
    common_parser.add_argument("--dashboard", action="store_true", help="Generate dashboard PNG")
    common_parser.add_argument("--stats", action="store_true", help="Print statistics")
    common_parser.add_argument(
        "--format", choices=["json", "csv"], default="json", help="Output format for stats"
    )
    common_parser.add_argument(
        "--sampling-rate", type=float, default=100.0, help="Sampling rate in Hz"
    )

    # Lorenz subparser
    lorenz_parser = subparsers.add_parser(
        "lorenz", parents=[common_parser], help="Lorenz attractor"
    )
    lorenz_parser.add_argument("--a", type=float, default=10.0)
    lorenz_parser.add_argument("--b", type=float, default=28.0)
    lorenz_parser.add_argument("--c", type=float, default=8.0 / 3.0)
    lorenz_parser.add_argument("--dt", type=float, default=0.01)
    lorenz_parser.add_argument("--x", type=float, default=0.01)
    lorenz_parser.add_argument("--y", type=float, default=0.0)
    lorenz_parser.add_argument("--z", type=float, default=0.3)
    lorenz_parser.add_argument("--iterations", type=int, default=1000)
    lorenz_parser.add_argument("--variable", default="x", choices=["x", "y", "z"])
    lorenz_parser.add_argument(
        "--delay-steps", type=int, default=0, help="Sensor delay in time steps"
    )
    lorenz_parser.add_argument("--noise", type=float, default=0.0, help="Measurement noise std")

    # Sinusoid subparser
    sinusoid_parser = subparsers.add_parser(
        "sinusoid", parents=[common_parser], help="Sinusoidal signals"
    )
    sinusoid_parser.add_argument("--ph0-a", type=float, default=0)
    sinusoid_parser.add_argument("--ph0-b", type=float, default=0)
    sinusoid_parser.add_argument("--frq-a", type=float, default=1)
    sinusoid_parser.add_argument("--frq-b", type=float, default=1)
    sinusoid_parser.add_argument("--pers", type=int, default=1)
    sinusoid_parser.add_argument("--delay-a", type=float, default=0)
    sinusoid_parser.add_argument("--delay-b", type=float, default=0)
    sinusoid_parser.add_argument("--iterations", type=int, default=1000)

    # Coupled oscillator subparser
    coupled_parser = subparsers.add_parser(
        "coupled", parents=[common_parser], help="Coupled oscillators (Kuramoto)"
    )
    coupled_parser.add_argument("--coupling", type=float, default=0.5)
    coupled_parser.add_argument("--freqs", nargs="+", type=float, default=[1.0, 1.05])
    coupled_parser.add_argument("--duration", type=float, default=100.0)
    coupled_parser.add_argument("--dt", type=float, default=0.01)
    coupled_parser.add_argument("--noise", type=float, default=0.0, help="Noise standard deviation")

    # Parquet subparser
    parquet_parser = subparsers.add_parser(
        "parquet", parents=[common_parser], help="Parquet file data"
    )
    parquet_parser.add_argument("--file", required=True, help="Parquet file path")
    parquet_parser.add_argument("--col-a", required=True, help="Column A name")
    parquet_parser.add_argument("--col-b", required=True, help="Column B name")
    parquet_parser.add_argument("--start", type=int, default=0)
    parquet_parser.add_argument("--end", type=int, default=None)
    parquet_parser.add_argument("--window", type=int, default=60)
    parquet_parser.add_argument("--lag", type=int, default=None)

    # Belousov-Zhabotinsky subparser
    bz_parser = subparsers.add_parser(
        "bz", parents=[common_parser], help="Belousov-Zhabotinsky oscillator (Oregonator model)"
    )
    bz_parser.add_argument(
        "--f", dest="bz_f", type=float, default=1.0, help="Stoichiometric parameter f"
    )
    bz_parser.add_argument("--q", dest="bz_q", type=float, default=0.05, help="Small parameter q")
    bz_parser.add_argument(
        "--eps", dest="bz_eps", type=float, default=0.02, help="Time-scale separation parameter eps"
    )
    bz_parser.add_argument(
        "--dt", dest="bz_dt", type=float, default=0.01, help="Integration time step"
    )
    bz_parser.add_argument("--x0", dest="bz_x0", type=float, default=0.1, help="Initial x value")
    bz_parser.add_argument("--z0", dest="bz_z0", type=float, default=0.1, help="Initial z value")
    bz_parser.add_argument(
        "--iterations",
        dest="bz_iterations",
        type=int,
        default=10000,
        help="Number of integration steps",
    )
    bz_parser.add_argument(
        "--variable",
        dest="bz_variable",
        default="x",
        choices=["x", "z"],
        help="Variable to extract",
    )
    bz_parser.add_argument(
        "--delay-steps",
        dest="bz_delay_steps",
        type=int,
        default=100,
        help="Sensor delay in time steps",
    )
    bz_parser.add_argument(
        "--noise", dest="bz_noise", type=float, default=0.05, help="Measurement noise std"
    )
    bz_parser.add_argument(
        "--transient",
        dest="bz_transient",
        type=int,
        default=2000,
        help="Transient steps to discard",
    )

    args = parser.parse_args()

    try:
        # Create data source
        source = create_source(args)

        # Run pipeline
        pipeline = SynchronizationPipeline(source).run()

        # Print stats
        if args.stats:
            stats = pipeline.get_stats()
            if args.format == "json":
                print(json.dumps(stats, indent=2))
            else:
                for k, v in stats.items():
                    print(f"{k}: {v:.6f}")

        # Export results
        output_dir = Path(args.output)
        export_results(pipeline, str(output_dir))

    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
