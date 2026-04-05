#!/usr/bin/env python3
"""
CLI script to run the full dental AI pipeline on a single OPG.

Usage:
    python scripts/run_inference.py --image path/to/opg.jpg --output report.json

Pipeline:
    OPG → YOLO tooth detection → FDI assignment
        → Tight crop → Caries model (collaborator)
        → Expanded crop → Bone loss model
        → Filter + Report assembly

Status: PLACEHOLDER — requires all models to be trained and integrated.
"""

import argparse


def main():
    parser = argparse.ArgumentParser(description="Run full dental AI pipeline")
    parser.add_argument("--image", type=str, required=True, help="Path to OPG X-ray")
    parser.add_argument("--output", type=str, default="report.json", help="Output report path")
    args = parser.parse_args()

    print("=" * 60)
    print("DENTAL AI PIPELINE — FULL INFERENCE")
    print("=" * 60)
    print(f"Input:  {args.image}")
    print(f"Output: {args.output}")
    print()
    print("Status: Not yet implemented.")
    print("Requires: YOLO model + Caries model + Bone loss model")
    print("=" * 60)


if __name__ == "__main__":
    main()
