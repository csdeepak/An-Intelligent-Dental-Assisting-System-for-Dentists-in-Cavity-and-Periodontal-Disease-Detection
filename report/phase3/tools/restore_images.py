"""Restore the images kept out of git (report/phase3/.gitignore) before building from a fresh clone.

The 13 Phase 2 images below are byte copies of the media in the Phase 2 report's .docx: ten figures
reproduced from the reviewed papers (third-party) and three Tufts radiograph crops (Tufts licence: no
redistribution). Each is checked against its SHA-256 prefix after extraction.

The three app screenshots (figures/screens/) cannot be extracted: they were captured from the Streamlit
demo (`app.py`) running on DENTEX `test_0`, with the browser pane at desktop width, on 6 Nov 2026 (landing
page, results, limitations block). Without them, and without any image here, the build still succeeds and
shows a framed placeholder (\\optionalgraphics in preamble.tex).

    python -I tools/restore_images.py [path/to/PW26_MHR_06_Report.docx]
"""
import hashlib
import sys
import zipfile
from pathlib import Path

HERE = Path(__file__).resolve().parents[1]
DOCX = Path(sys.argv[1]) if len(sys.argv) > 1 else Path.home() / "Downloads" / "PW26_MHR_06_Report.docx"
# figures/phase2/<name> <- word/media/<member>, SHA-256 prefix
MEDIA = {
    "p2_2_01_yolov7_cbam.jpg": ("image5.jpg", "c80245ffb6ad"),
    "p2_2_02_intraoral_pipeline.jpg": ("image20.jpg", "c2534685046c"),
    "p2_2_03_periodontal_dual_yolo.jpg": ("image12.jpg", "0c203e5ced8f"),
    "p2_2_04_nested_unet.jpg": ("image10.jpg", "d082fcc07834"),
    "p2_2_05_two_stage_pipeline.jpg": ("image7.jpg", "9bd9aa047b55"),
    "p2_2_06_yolo_panoramic.jpg": ("image9.jpg", "007d84585ba5"),
    "p2_2_07_unet_pediatric.jpg": ("image1.jpg", "fded03792993"),
    "p2_2_09_ai_dentify.jpg": ("image8.jpg", "8e0f4c65cacb"),
    "p2_2_10_aap_efp_2018.jpg": ("image4.jpg", "572379d29afc"),
    "p2_2_11_ai_caries_overview.jpg": ("image15.jpg", "e26b7534bf66"),
    "p2_5_01_crop_validation_grid.jpg": ("image25.jpg", "d7b55df1921a"),
    "p2_5_02_crop_samples.jpg": ("image11.jpg", "5ec505d8376f"),
    "p2_5_03_cej_overlays.jpg": ("image21.jpg", "e788b985d63a"),
}

if not DOCX.exists():
    sys.exit(f"Phase 2 report not found: {DOCX}")
out = HERE / "figures" / "phase2"
out.mkdir(parents=True, exist_ok=True)
with zipfile.ZipFile(DOCX) as z:
    for name, (member, prefix) in MEDIA.items():
        data = z.read("word/media/" + member)
        digest = hashlib.sha256(data).hexdigest()
        if not digest.startswith(prefix):
            sys.exit(f"{member}: SHA-256 {digest[:12]} does not match {prefix}; is this the Phase 2 report?")
        (out / name).write_bytes(data)
        print(f"restored figures/phase2/{name}")
screens = sorted((HERE / "figures" / "screens").glob("app_0*.jpg")) if (HERE / "figures" / "screens").exists() else []
print(f"{len(MEDIA)} Phase 2 images restored; app screenshots present: {len(screens)} of 3"
      + ("" if len(screens) == 3 else " (recapture them as described in this script's docstring)"))
