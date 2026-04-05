# Models Directory

Trained model checkpoints are stored here. **Model files (.pth, .pt) are git-ignored** due to file size.

## Expected Files After Training

```
models/
  bone_loss_resnet18_best.pth    ← Best checkpoint (by val F1)
  bone_loss_resnet18_final.pth   ← Final epoch checkpoint
  training_history.json           ← Loss/metric curves per epoch
```

## Model Specifications

| Property | Value |
|----------|-------|
| Architecture | ResNet18 (pretrained ImageNet) |
| Input | 224×224 expanded crop (1.5× W, 2.0× H) |
| Output | Binary — Bone loss Present / Absent |
| FC layer | 512 → 2 |
| Normalization | ImageNet mean/std |
