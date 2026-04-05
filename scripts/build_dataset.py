#!/usr/bin/env python3
"""
CLI script to build the bone loss training dataset.

Usage:
    python scripts/build_dataset.py --config configs/dataset_config.yaml

For Colab/Kaggle, use the notebook instead:
    notebooks/02_dataset_construction.ipynb
"""

import argparse
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))


def main():
    parser = argparse.ArgumentParser(description="Build bone loss training dataset")
    parser.add_argument("--config", type=str, default="configs/dataset_config.yaml",
                        help="Path to config YAML")
    parser.add_argument("--threshold", type=float, default=None,
                        help="Override overlap threshold")
    args = parser.parse_args()

    print("=" * 60)
    print("BONE LOSS DATASET CONSTRUCTION")
    print("=" * 60)
    print(f"Config: {args.config}")
    print()
    print("For full interactive pipeline with visual validation,")
    print("use the notebook: notebooks/02_dataset_construction.ipynb")
    print()
    print("This CLI script is a placeholder for future automation.")
    print("=" * 60)


if __name__ == "__main__":
    main()
