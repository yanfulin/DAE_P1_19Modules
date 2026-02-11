#!/usr/bin/env python3
"""
demo_v14_simulator.py
V1.4 Demo Simulator CLI Entry Point
"""

from dae_p1.M22_demo_v14_simulator import V14DemoSimulator
import argparse
import sys


def main():
    """Main entry point for V1.4 Demo Simulator"""
    parser = argparse.ArgumentParser(
        description='DAE P1 V1.4 Demo Simulator - Generate 10 test cases'
    )
    parser.add_argument(
        '--output-dir',
        default='demo_output_v14',
        help='Output directory for generated files (default: demo_output_v14)'
    )
    parser.add_argument(
        '--config',
        default=None,
        help='Path to privacy config file (optional)'
    )

    args = parser.parse_args()

    try:
        # Initialize simulator
        print(f"Initializing V1.4 Demo Simulator...")
        sim = V14DemoSimulator(config_path=args.config)

        # Run all test cases
        print(f"Generating test cases to: {args.output_dir}/\n")
        results = sim.run_all_cases(output_dir=args.output_dir)

        # Count egress receipts
        egress_count = sum(1 for r in results if r.get('egress_receipt'))

        # Print summary
        print(f"\n{'='*60}")
        print(f"V1.4 Demo Simulator - Summary")
        print(f"{'='*60}")
        print(f"Generated {len(results)} test cases in {args.output_dir}/")
        print(f"  proof_cards/: {len(results)} JSON files")
        print(f"  egress_receipts/: {egress_count} JSON files")
        print(f"  summary.csv: Test case summary")
        print(f"{'='*60}\n")

        return 0

    except Exception as e:
        print(f"ERROR: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
