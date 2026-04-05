"""
Visualization utilities for the dental AI pipeline.

Includes:
  - Mask overlay on crops
  - Overlap distribution plots
  - Sample grids
  - Training history curves
"""

import cv2
import numpy as np
import matplotlib.pyplot as plt


def create_mask_overlay(crop, mask_crop, alpha=0.4):
    """
    Overlay expert mask on tooth crop.
    Mask regions shown in red.

    Args:
        crop: Grayscale 224×224 crop
        mask_crop: Grayscale mask cropped to same region
        alpha: Transparency for non-mask regions (0=transparent, 1=opaque)

    Returns:
        RGB overlay image
    """
    overlay = cv2.cvtColor(crop, cv2.COLOR_GRAY2RGB)
    mask_bin = (mask_crop > 0)

    overlay[mask_bin, 0] = np.minimum(
        overlay[mask_bin, 0].astype(int) + 120, 255
    ).astype(np.uint8)
    overlay[mask_bin, 1] = (overlay[mask_bin, 1] * alpha).astype(np.uint8)
    overlay[mask_bin, 2] = (overlay[mask_bin, 2] * alpha).astype(np.uint8)

    return overlay


def plot_overlap_distribution(overlaps, threshold, save_path=None):
    """
    Plot overlap score distribution with threshold line.

    Args:
        overlaps: Array of overlap scores
        threshold: Current decision threshold
        save_path: Optional path to save figure
    """
    fig, axes = plt.subplots(1, 3, figsize=(18, 5))

    axes[0].hist(overlaps, bins=50, color='steelblue',
                 edgecolor='black', alpha=0.7)
    axes[0].axvline(threshold, color='red', ls='--', lw=2,
                    label=f'T={threshold}')
    axes[0].set_title('All overlap scores')
    axes[0].legend()

    low = overlaps[overlaps < 0.05]
    axes[1].hist(low, bins=50, color='coral', edgecolor='black', alpha=0.7)
    axes[1].axvline(threshold, color='red', ls='--', lw=2)
    axes[1].set_title('Zoomed: < 0.05')

    nonzero = overlaps[overlaps > 0]
    if len(nonzero) > 0:
        axes[2].hist(np.log10(nonzero), bins=50, color='seagreen',
                     edgecolor='black', alpha=0.7)
        axes[2].axvline(np.log10(threshold), color='red', ls='--', lw=2)
        axes[2].set_title('Log-scale (nonzero)')

    plt.tight_layout()
    if save_path:
        plt.savefig(save_path, dpi=150, bbox_inches='tight')
    plt.show()


def plot_training_history(history, save_path=None):
    """
    Plot training and validation loss/F1 curves.

    Args:
        history: Dict with keys 'train_loss', 'val_loss', 'val_f1'
        save_path: Optional path to save figure
    """
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 5))

    ax1.plot(history['train_loss'], label='Train Loss')
    ax1.plot(history['val_loss'], label='Val Loss')
    ax1.set_xlabel('Epoch')
    ax1.set_ylabel('Loss')
    ax1.set_title('Loss Curves')
    ax1.legend()

    ax2.plot(history['val_f1'], label='Val F1 (macro)', color='green')
    ax2.set_xlabel('Epoch')
    ax2.set_ylabel('F1 Score')
    ax2.set_title('Validation F1')
    ax2.legend()

    plt.tight_layout()
    if save_path:
        plt.savefig(save_path, dpi=150, bbox_inches='tight')
    plt.show()
