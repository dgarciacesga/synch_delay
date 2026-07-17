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
    ParquetDataSource,
    SynchronizationPipeline,
    export_results,
)


def create_source(args):
    """Create data source from command line arguments."""
    if args.type == "lorenz":
        return LorenzDataSource(
            a=args.a, b=args.b, c=args.c, dt=args.dt,
            initial_values_1=[args.x1, args.y1, args.z1],
            initial_values_2=[args.x2, args.y2, args.z2],
            iterations=args.iterations,
            variable=args.variable,
            sampling_rate=args.sampling_rate,
        )
    elif args.type == "sinusoid":
        return SinusoidDataSource(
            ph0_a=args.ph0_a, ph0_b=args.ph0_b,
            frq_a=args.frq_a, frq_b=args.frq_b,
            pers=args.pers, delay_a=args.delay_a, delay_b=args.delay_b,
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
    else:
        raise ValueError(f"Unknown source type: {args.type}")


def main():
    parser = argparse.ArgumentParser(
        description="Synchronization Analysis using Kuramoto Order Parameter",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Lorenz attractor
  synch-analysis lorenz --iterations 1000 --output results/
  
  # Sinusoidal signals with phase delay
  synch-analysis sinusoid --delay-b 3 --output results/
  
  # Coupled oscillators
  synch-analysis coupled --coupling 0.8 --freqs 1.0,1.05 --output results/
  
  # Parquet data
  synch-analysis parquet --file data.pqt --col-a Temp1 --col-b Temp2 --output results/
        """
    )
    parser.add_argument("type", choices=["lorenz", "sinusoid", "coupled", "parquet"],
                        help="Data source type")
    parser.add_argument("--output", "-o", default="results", help="Output directory")
    parser.add_argument("--dashboard", action="store_true", help="Generate dashboard PNG")
    parser.add_argument("--stats", action="store_true", help="Print statistics")
    parser.add_argument("--format", choices=["json", "csv"], default="json",
                        help="Output format for stats")

    # Lorenz arguments
    parser.add_argument("--a", type=float, default=10.0)
    parser.add_argument("--b", type=float, default=28.0)
    parser.add_argument("--c", type=float, default=8.0/3.0)
    parser.add_argument("--dt", type=float, default=0.01)
    parser.add_argument("--x1", type=float, default=0.01)
    parser.add_argument("--y1", type=float, default=0.0)
    parser.add_argument("--z1", type=float, default=0.3)
    parser.add_argument("--x2", type=float, default=0.2)
    parser.add_argument("--y2", type=float, default=0.1)
    parser.add_argument("--z2", type=float, default=0.4)
    parser.add_argument("--iterations", type=int, default=1000)
    parser.add_argument("--variable", default="x")
    parser.add_argument("--sampling-rate", type=float, default=100.0)

    # Sinusoid arguments
    parser.add_argument("--ph0-a", type=float, default=0)
    parser.add_argument("--ph0-b", type=float, default=0)
    parser.add_argument("--frq-a", type=float, default=1)
    parser.add_argument("--frq-b", type=float, default=1)
    parser.add_argument("--pers", type=int, default=1)
    parser.add_argument("--delay-a", type=float, default=0)
    parser.add_argument("--delay-b", type=float, default=0)

    # Coupled oscillator arguments
    parser.add_argument("--coupling", type=float, default=0.5)
    parser.add_argument("--freqs", nargs="+", type=float, default=[1.0, 1.05])
    parser.add_argument("--duration", type=float, default=100.0)
    parser.add_argument("--noise", type=float, default=0.0)

    # Parquet arguments
    parser.add_argument("--file", help="Parquet file path")
    parser.add_argument("--col-a", help="Column A name")
    parser.add_argument("--col-b", help="Column B name")
    parser.add_argument("--start", type=int, default=0)
    parser.add_argument("--end", type=int, default=None)
    parser.add_argument("--window", type=int, default=60)
    parser.add_argument("--lag", type=int, default=None)

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