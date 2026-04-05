# Data Directory

This directory stores processed datasets. **Raw data and processed crops are git-ignored** due to file size.

## Expected Structure After Running Dataset Construction

```
data/
  processed_dataset_tufts/
    train/
      0/    ← Normal tooth crops (224×224 PNG)
      1/    ← Diseased tooth crops (224×224 PNG)
    val/
      0/
      1/
    metadata/
      train_metadata.csv
      val_metadata.csv
    overlap_analysis.png
    visual_validation.png
    sample_grid.png
```

## Raw Dataset Location

The Tufts Dental Dataset should be stored on Google Drive (not in this repo):

```
Google Drive/tufts/ZIP/
  Radiographs/Radiographs/
  Segmentation/Segmentation/
  Expert/Expert/
```
