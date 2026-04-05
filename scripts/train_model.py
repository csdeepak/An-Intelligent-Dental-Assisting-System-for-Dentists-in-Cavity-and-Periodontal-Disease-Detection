#!/usr/bin/env python3
"""
CLI script to train the bone loss ResNet18 model.

Usage:
    python scripts/train_model.py --config configs/dataset_config.yaml

For Colab/Kaggle with GPU, use the notebook instead:
    notebooks/03_model_training.ipynb

Status: PLACEHOLDER — will be implemented after dataset construction is validated.
"""

import argparse


def main():
    parser = argparse.ArgumentParser(description="Train bone loss classifier")
    parser.add_argument("--config", type=str, default="configs/dataset_config.yaml")
    parser.add_argument("--epochs", type=int, default=50)
    parser.add_argument("--lr", type=float, default=1e-4)
    parser.add_argument("--batch-size", type=int, default=16)
    args = parser.parse_args()

    print("=" * 60)
    print("BONE LOSS MODEL TRAINING")
    print("=" * 60)
    print(f"Config: {args.config}")
    print(f"Epochs: {args.epochs}, LR: {args.lr}, Batch: {args.batch_size}")
    print()
    print("Status: Not yet implemented.")
    print("Complete dataset construction and validation first.")
    print("=" * 60)


if __name__ == "__main__":
    main()
