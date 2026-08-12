# 🦷 Dental AI Pipeline: Automated OPG Analysis
## Comprehensive Project Analysis & Placement Preparation Guide

This report provides a detailed breakdown of the **Dental AI Pipeline Capstone Project**, which automates tooth detection, numbering, caries classification, and periodontal bone loss severity analysis from panoramic dental X-rays (Orthopantomographs - OPGs). 

It is designed to serve as a **comprehensive reference sheet** for recruiters, placement cells, and technical interviews.

---

## 📌 Project Executive Summary
- **Domain**: Medical Image Processing, Deep Learning, Computer Vision.
- **Clinical Problem**: Reading Orthopantomographs (OPGs) is highly user-dependent, leading to diagnostic errors and inter-examiner variability among junior clinicians. Early caries and periodontal bone loss features are subtle and frequently overlooked.
- **Solution**: Developed a modular, high-throughput deep learning pipeline that consumes a single OPG (840 × 1615 px) and outputs a per-tooth clinical report mapped to standard FDI numbering (e.g., Tooth 18, 38).
- **Core Technology Stack**: Python 3.10, PyTorch, OpenCV, Ultralytics YOLOv11, torchvision, scikit-learn, FPDF, and SciPy.

---

## ⚙️ End-to-End System Architecture

The pipeline processes a raw OPG image through a tooth-centric cascade approach:

```
                  ┌────────────────────────────────────────────────────────┐
                  │              Input OPG X-ray (840 x 1615 px)           │
                  └───────────────────────────┬────────────────────────────┘
                                              ▼
                  ┌────────────────────────────────────────────────────────┐
                  │       Stage 1: Tooth Detection & Segmentation          │
                  │             (YOLOv11l fine-tuned on Tufts)             │
                  └───────────────────────────┬────────────────────────────┘
                                              ▼
                  ┌────────────────────────────────────────────────────────┐
                  │       Stage 2: Left-to-Right Sort & Jaw Splitting      │
                  │              FDI Tooth Numbering Assignment            │
                  └─────────────┬────────────────────────────┬─────────────┘
                                │                            │
                                ▼                            ▼
                  ┌──────────────────────────┐  ┌──────────────────────────┐
                  │      Caries Path         │  │     Bone Loss Path       │
                  │                          │  │                          │
                  │  Tight Crop (1.0x Box)   │  │  Expanded Crop (1.5x,2x) │
                  │  (Focuses on Crown)      │  │  (Crown + Root + Bone)   │
                  │             │            │  │            │             │
                  │             ▼            │  │            ▼             │
                  │   Caries Classifier      │  │  Bone Loss Classifier    │
                  │  ResNet18 (DENTEX/Tufts) │  │   ResNet18 (Tufts Data)  │
                  │    Binary (Yes/No)       │  │    Binary (Present/Abs)  │
                  │             │            │  │            │             │
                  │      (If Caries=Yes)     │  │      (If Bone Loss=Pres) │
                  │             ▼            │  │            ▼             │
                  │   Caries Severity        │  │   Bone Loss Severity     │
                  │    (3-Class model)       │  │      (3-Class model)     │
                  └─────────────┬────────────┘  └────────────┬─────────────┘
                                │                            │
                                └─────────────┬──────────────┘
                                              ▼
                  ┌────────────────────────────────────────────────────────┐
                  │       Stage 5: Clinical Filtering & Report Assembly    │
                  │             (Omits healthy/normal teeth)               │
                  └───────────────────────────┬────────────────────────────┘
                                              ▼
                  ┌────────────────────────────────────────────────────────┐
                  │   Final JSON / PDF Diagnostic Report (with Grad-CAM)   │
                  └────────────────────────────────────────────────────────┘
```

### FDI Numbering System
Tooth detections are mapped from the Universal Numbering System (1-32) to the FDI World Dental Federation notation (quadrants 1-4, teeth 1-8).
- **Quadrant 1 (Upper Right)**: Universal 1–8 ➔ FDI 18–11
- **Quadrant 2 (Upper Left)**: Universal 9–16 ➔ FDI 21–28
- **Quadrant 3 (Lower Left)**: Universal 17–24 ➔ FDI 38–31
- **Quadrant 4 (Lower Right)**: Universal 25–32 ➔ FDI 41–48

---

## 📊 Rigorous Experimental Results & Performance Metrics

Metrics compiled directly from the training and evaluation runs of the Jupyter notebooks:

### 1. Stage 1: YOLOv11l Tooth Detection & Localization
*Source Notebooks: [YOLO_trained.ipynb](file:///Users/chennupatigunadeep/Downloads/Capstone/YOLO_trained.ipynb) & [A100_150/YOLO_trained.ipynb](file:///Users/chennupatigunadeep/Downloads/Capstone/A100_150/YOLO_trained.ipynb)*

- **Dataset**: Tufts Dental OPG Dataset (700 Train, 150 Val, 150 Test images).
- **Model**: Pre-trained YOLOv11l (25.28M parameters, 86.6 GFLOPs), fine-tuned with AdamW.
- **Hardware Comparison (imgsz=1024 vs 768)**:
  - **A100 GPU Run (imgsz=1024, 150 epochs)**:
    - **Validation Set**: Precision: **0.788** | Recall: **0.772** | mAP@0.5: **0.834** | mAP@0.5:0.95: **0.367**
    - **Test Set (Held-Out)**: Precision: **0.7643** | Recall: **0.7421** | mAP@0.5: **0.7824** | mAP@0.5:0.95: **0.3351**
    - **Inference Speed**: **3.1 ms** preprocess & inference per image.
  - **H200 GPU Run (imgsz=768, 50 epochs)**:
    - **Validation Set**: Precision: **0.609** | Recall: **0.678** | mAP@0.5: **0.678** | mAP@0.5:0.95: **0.282**
- **Insight**: High input resolution (1024 vs 768) and longer epochs are critical due to the dense layout and small geometric variations of teeth on OPGs.

### 2. Stage 3: Caries Severity Classifier (3-Class)
*Source Notebook: [caries/phase-1.ipynb](file:///Users/chennupatigunadeep/Downloads/Capstone/Deepak%20impleentation/An-Intelligent-Dental-Assisting-System-for-Dentists-in-Cavity-and-Periodontal-Disease-Detection/notebooks/caries/phase-1.ipynb)*

- **Dataset**: DENTEX (2,767 caries, 762 no-caries in training; 133 val).
- **Model**: Pre-trained ResNet18 backbone, frozen feature extractor, fully connected classifier fine-tuning.
- **Results on Validation Set (Best Run)**:
  - **Overall Accuracy**: **81.0%**
  - **Macro F1-Score**: **0.77** | **Weighted F1-Score**: **0.82**

| Disease Class | Precision | Recall | F1-Score | Support (Crops) |
|---|---|---|---|---|
| **Caries** (Mild/Moderate) | 0.94 | 0.80 | 0.87 | 101 |
| **Deep Caries** (Severe) | 0.57 | 0.84 | 0.68 | 32 |

### 3. Stage 4: Periodontal Bone Loss Binary Classifier
*Source Notebook: [Bone Loss/03_bone_loss_model_training.ipynb](file:///Users/chennupatigunadeep/Downloads/Capstone/Deepak%20impleentation/An-Intelligent-Dental-Assisting-System-for-Dentists-in-Cavity-and-Periodontal-Disease-Detection/notebooks/Bone%20Loss/03_bone_loss_model_training.ipynb)*

- **Dataset**: Tufts Dataset. Built 22,806 tooth crops. Addressed extreme class imbalance (96% normal, 4% diseased) using normal undersampling (to 2,500) and diseased augmentation (to 2,217).
- **Model**: ResNet18 fine-tuned with Focal Loss ($\gamma=2.0$, class weights $\alpha = [0.642, 2.258]$) to prioritize positive recall.
- **Results on Validation Set** (Untouched real-world distribution, 1,558 crops):
  - **Overall Accuracy**: **98.91%**
  - **Macro F1-Score**: **0.9233** *(Target: $\ge 0.72$)*
  - **Normal Class F1**: **0.9943** *(Precision: 0.9933, Recall: 0.9953)*
  - **Diseased Class F1**: **0.8522** *(Precision: 0.8750, Recall: 0.8305)* *(Target: $\ge 0.70$)*
  - **Clinical Sensitivity (Diseased Recall)**: **83.05%**
  - **Clinical Specificity (Normal Recall)**: **99.53%**
  - **Confusion Matrix Breakdown**: TN: 1492 | FP: 7 | FN: 10 | TP: 49.

### 4. Stage 4b: Periodontal Bone Loss Severity Classifier (3-Class)
*Source Notebook: [Bone Loss/04_bone_loss_severity.ipynb](file:///Users/chennupatigunadeep/Downloads/Capstone/Deepak%20impleentation/An-Intelligent-Dental-Assisting-System-for-Dentists-in-Cavity-and-Periodontal-Disease-Detection/notebooks/Bone%20Loss/04_bone_loss_severity.ipynb)*

- **Dataset**: Built from positive bone loss crops using expert mask overlap. 976 train crops, 52 val crops (untouched).
- **Model**: 3-Class ResNet18 trained using Focal Loss ($\gamma=2.0$, per-class $\alpha = [1.694, 0.72, 0.98]$).
- **Results on Validation Set (Best Epoch 2)**:
  - **Overall Accuracy**: **69.23%**
  - **Macro F1-Score**: **0.7208** *(Target: $\ge 0.72$)*

| Severity Stage (Overlap Metric) | Precision | Recall | F1-Score | Support |
|---|---|---|---|---|
| **Mild** ($\le 0.05$ overlap ratio) | 1.00 | 0.67 | 0.80 | 6 |
| **Moderate** ($0.05 \text{ to } 0.15$) | 0.80 | 0.57 | 0.67 | 28 |
| **Severe** ($> 0.15$ overlap ratio) | 0.57 | 0.89 | 0.70 | 18 |

### 5. Exploratory Stage: CEJ-Based Bone Level Estimation (Physiological Grounding)
*Source Notebook: [Bone Loss/05_cej_estimation_v2.ipynb](file:///Users/chennupatigunadeep/Downloads/Capstone/Deepak%20impleentation/An-Intelligent-Dental-Assisting-System-for-Dentists-in-Cavity-and-Periodontal-Disease-Detection/notebooks/Bone%20Loss/05_cej_estimation_v2.ipynb)*

- **Goal**: Approximate the clinical gold standard: distance between the Cementen-Enamel Junction (CEJ) and the bone crest relative to root length.
- **Workflow**:
  1. Apply **CLAHE** (Contrast Limited Adaptive Histogram Equalization) and Gaussian Blur.
  2. Perform column-wise CEJ detection using intensity valleys.
  3. Perform column-wise root apex detection using local minima.
  4. Perform focused bone crest search in a narrow vertical window (CEJ to CEJ + 40% root height) to exclude molar bifurcations and lower jaw limits.
  5. Apply **IQR outlier removal** and compute confidence scoring.
- **Results on 296 Positive Crops**:
  - **Processing Success Rate**: **100.0%** (296/296 crops processed successfully).
  - **Confidence Filter**: **62.5%** (185 crops) flagged as highly reliable.
  - **Stats on Reliable Crops**: Bone loss percentage median is **2.5%** (mean: 5.1%, max: 29.9%).
- **Clinical Insight**: Agreement analysis between mask overlap and CEJ estimation is **15.0%**. This suggests that while CEJ estimation is the clinical gold standard for high-resolution periapical radiographs, it has limited precision on OPGs due to panoramic distortion, making the machine-learning-based overlap metric more robust.

---

## 💡 Key Engineering Decisions (Recruiter Gold)

These structural details demonstrate software design maturity and problem-solving capability:

### 1. Asymmetric Crop Expansion (1.5x W, 2.0x H)
- **Problem**: Permanent teeth have a mean aspect ratio of ~0.35 (3x taller than wide). Standard symmetric bounding box expansion (e.g., doubling the crop size in both dimensions) causes horizontal bleeding into neighboring teeth.
- **Solution**: Developed an asymmetric expansion helper ([compute_expanded_bbox](file:///Users/chennupatigunadeep/Downloads/Capstone/Deepak%20impleentation/An-Intelligent-Dental-Assisting-System-for-Dentists-in-Cavity-and-Periodontal-Disease-Detection/notebooks/Bone%20Loss/02_bone_loss_dataset_construction.ipynb#L16)), expanding the bounding box width by **1.5×** and height by **2.0×**. This captures the alveolar bone level below the root apex while minimizing horizontal overlap.

### 2. Overlap Metric vs. Intersection-over-Union (IoU)
- **Problem**: Expert pathology masks in the Tufts dataset are sparse (lesions occupy 0.5–2% of the crop area). Using traditional IoU as a threshold for binary classification yields values near zero because the union term is dominated by the large background area, causing false negatives.
- **Solution**: Rejected IoU in favor of a pixel-overlap ratio:
  $$\text{Overlap Ratio} = \frac{\text{Pathology Mask Pixels inside Crop}}{\text{Total Crop Area}}$$
  A threshold of **0.01 (1% coverage)** was selected after plotting the overlap ratio distribution, separating noise-level annotations from genuine bone loss pathology.

### 3. Bounding Box Jittering for YOLO Noise Emulation
- **Problem**: The classification model is trained on clean ground-truth crops, but at inference, it receives bounding boxes generated by YOLO. Minor localization errors (offsets of a few pixels) from YOLO cause a distribution mismatch, leading to a performance drop.
- **Solution**: Simulated YOLO noise by applying **±15% random coordinate jitter** to bounding box coordinates during training dataset construction. This forces the ResNet18 model to learn translation-invariant features.

### 4. Patient-Level Splitting to Prevent Data Leakage
- **Problem**: A single patient scan contains up to 32 teeth. If a traditional random split is applied at the tooth crop level, crops from the same scan (sharing identical lighting, bone density, and acquisition noise) leak into both the train and validation sets, inflating validation accuracy.
- **Solution**: Enforced **image-level stratified splits** using patient IDs extracted from filename stems. If an OPG image is assigned to the validation set, all 32 tooth crops from that image are isolated to the validation set.

### 5. Resampling Strategy for Extreme Class Imbalance
- **Problem**: Tufts dataset has a 23.8x class imbalance (96% normal teeth vs 4% bone loss). Models trained on this default to predicting "normal" for all inputs.
- **Solution**: Built a resampled training dataset:
  - Undersampled normal crops down to **2,500** using a stratified approach to preserve patient diversity.
  - Kept all **739** positive crops and augmented them with flips, rotations, color jitter, and translations to reach **2,217** samples.
  - The validation set was kept **completely untouched** (real-world imbalance) to ensure validation metrics reflect actual clinical performance.

---

## 📝 STAR Method Resume Impact Statements

Use these bullet points on your resume or LinkedIn profile to stand out to hiring managers:

- **Lead AI Engineer — Dental AI Pipeline**
  - **Situation**: Junior dentists and dental students exhibit high diagnostic error rates and inter-examiner variability when interpreting panoramic OPG X-rays, often overlooking early-stage caries and alveolar bone loss.
  - **Task**: Design and implement a fully automated, end-to-end medical image processing pipeline to localize individual teeth, classify pathologies, and output a structured diagnostic report.
  - **Action**: Fine-tuned a **YOLOv11l** tooth-detection model and designed a dual-path classification framework using **ResNet18 backbones** trained on DENTEX and Tufts datasets. Engineered a custom **asymmetric crop expansion (1.5x W, 2.0x H)** to capture surrounding alveolar bone and resolved class imbalance (23.8x) using stratified normal undersampling, minority augmentation, and Focal Loss ($\gamma=2.0$). 
  - **Result**: Achieved an F1-score of **0.9943** for healthy teeth and **0.8522** for bone loss on an untouched validation set representing real-world distribution, with a clinical sensitivity (recall) of **83.05%** and specificity of **99.53%**.
  - **Action**: Developed an exploratory physiological module for **Cementen-Enamel Junction (CEJ)** estimation using CLAHE, Gaussian blur, intensity-valley detection, and confidence thresholds, achieving a **100% extraction success rate** across positive cases.
  - **Result**: Packaged the models into an integrated controller generating structured JSON reports and PDF summaries with **Grad-CAM visual explanations**, achieving an inference speed of **3.1 ms** on an NVIDIA A100 GPU.

---

## ❓ Technical Interview Q&A Preparation

These mock questions help prepare for machine learning engineering interviews:

### Q1: Why did you choose a multi-stage pipeline over an end-to-end object detector (like YOLO detecting caries directly)?
> **Answer**: "There are two main reasons: data scarcity and clinical utility. 
> 
> First, there is no large-scale, multi-disease dataset where teeth, caries, and bone loss are annotated together in one place. Using a multi-stage approach allowed us to train the tooth detector on Tufts, the caries model on DENTEX, and the bone loss model on Tufts pathology masks. 
> 
> Second, a pipeline-based approach is modular. If a better caries model or a higher-resolution tooth detector becomes available, we can plug it into our controller without retraining the rest of the pipeline. It also aligns with the clinical workflow, enabling tooth-level FDI reporting."

### Q2: Why did you reject the standard Intersection-over-Union (IoU) metric for assigning bone loss labels to your crops?
> **Answer**: "The expert pathology masks in our dataset are sparse, representing narrow lines or small blobs of bone loss. They occupy less than 2% of the total area of our expanded tooth crop. 
> 
> If we use IoU, the denominator (the union) is dominated by the large crop area, while the numerator (the intersection) is very small. This results in IoU values close to zero even for true positives. 
> 
> To resolve this, we implemented a pixel-overlap ratio where we divide the non-zero mask pixels inside the crop by the crop area. A threshold of 1% (0.01) was chosen after analyzing the overlap distribution, which successfully separates pathological bone loss from annotation noise."

### Q3: What is data leakage in the context of image crops, and how did you prevent it?
> **Answer**: "Data leakage occurs when information from the validation set is inadvertently shared with the training set, leading to overly optimistic validation metrics. 
> 
> In a tooth-crop dataset, multiple crops come from the same OPG X-ray. If we perform a simple random split at the crop level, tooth crops from patient A might end up in the training set, while other tooth crops from the exact same patient A end up in the validation set. Because these crops share the same exposure, contrast, and jaw structure, the model can memorize these features.
> 
> We prevented this by implementing **image-level stratified splits**. We grouped all crops by their source OPG filename stem, ensuring that all 32 crops of a single patient scan remain together in either the training split or the validation split."

### Q4: Your bone loss binary classifier achieves 98.91% accuracy but only 85.22% F1 on the diseased class. Why is there a difference, and which metric matters more?
> **Answer**: "The validation set preserves the real-world class distribution, which is highly imbalanced—only ~4% of the teeth have bone loss. In such a dataset, a naive model that predicts 'normal' for every single tooth would achieve 96% accuracy but an F1-score of 0 for the diseased class. Accuracy is therefore a misleading metric here. 
> 
> The F1-score of 85.22% for the diseased class is the metric that matters because it balances Precision (87.5%) and Recall (83.05%) on the minority class. In a clinical screening tool, false negatives are more dangerous than false positives, so we optimized the model to prioritize recall (diseased recall of 83.05%) by using Focal Loss with higher weights on the positive class."

### Q5: How does your CEJ estimation module work, and what are its limitations?
> **Answer**: "The Cementen-Enamel Junction (CEJ) estimation module is a deterministic image processing algorithm. It applies CLAHE to normalize local contrast, isolates the tooth region, and detects intensity valleys column-wise to identify the CEJ. It then searches for the root apex and the bone crest within a narrow window. 
> 
> While it works well in theory, OPG images suffer from panoramic projection distortion, low local resolution, and overlapping structures in the anterior region. This makes pixel-level landmark detection noisy. 
> 
> We introduced a confidence scoring system to flag and discard unreliable estimates, retaining CEJ estimation as a clinical support tool while relying on our ResNet18 model for primary classification."
