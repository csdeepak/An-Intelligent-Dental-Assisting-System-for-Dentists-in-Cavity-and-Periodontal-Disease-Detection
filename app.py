"""
Deployment demo: upload an OPG, see the per-tooth report and overlay in a browser.

WHAT THIS IS AND IS NOT
------------------------
This is a THIN WRAPPER around `scripts/run_inference.py` -- it calls `load_models` and
`run_pipeline` directly, the exact functions the CLI uses (verified byte-identical output
after the refactor that created them, RESULTS_LOG). There is no second implementation of the
pipeline here, so a fix or a limitation update in `run_inference.py` reaches this app for
free, and the app cannot silently drift from what the CLI proves out.

It is a single-user, unauthenticated, local demo for showing the pipeline working end to end
-- not a clinical tool, not multi-tenant, not hosted. It exists to satisfy the Phase III
"deployment" checklist item with something a reviewer can actually drive, not to be a product.

WHY THE LIMITATIONS ARE RENDERED, NOT LINKED
---------------------------------------------
`report["limitations"]` already carries the honest caveats (the detector recall and Stage-2
end-to-end accuracy of whichever detector ran, with a note on where those figures hold --
RESULTS_LOG 2026-10-11g for the default --
the caries caveat for whichever method ran, and that Stage 4 flags proximity to an abnormality
rather than periodontal bone loss). This
page puts that block directly under the results, same size as everything else, so it cannot
be screenshotted away from the numbers it qualifies.
"""

import sys
import threading
from pathlib import Path

import streamlit as st

REPO_ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(REPO_ROOT))

st.set_page_config(page_title="OPG Pipeline — Demo", page_icon="🦷", layout="wide")


@st.cache_resource(show_spinner="Loading models (first run only) …")
def get_models():
    """
    Cached across the whole app session -- loading is the slow part (~seconds) and must
    happen once, not per upload. Every default checkpoint is in git (since 13 Oct 2026), so a
    failure here means a weight file is missing or does not match its pinned sha256; it is
    caught and shown as a readable message, not a stack trace.
    """
    from scripts.run_inference import load_models
    try:
        return load_models()
    except SystemExit as e:
        return e


@st.cache_resource
def pipeline_lock():
    """One lock for the server. The cached models -- the YOLO predictors included -- are shared
    by every browser session, and two runs at once would share one predictor's state."""
    return threading.Lock()


def main():
    st.title("🦷 OPG Pipeline — Deployment Demo")
    st.caption(
        "Upload a panoramic dental X-ray. Runs the exact six-stage pipeline behind "
        "`scripts/run_inference.py` locally — no cloud call, no GPU required."
    )

    models = get_models()
    if isinstance(models, SystemExit):
        get_models.clear()      # not cached: once the weights are restored, a rerun loads them
        st.error(
            f"**Cannot start: {models}**\n\n"
            "Every default checkpoint is tracked in git: restore a missing or changed one with "
            "`git checkout -- models/`."
        )
        st.stop()
    models, device, paths = models

    uploaded = st.file_uploader("Upload an OPG", type=["png", "jpg", "jpeg"])
    if uploaded is None:
        st.info("Waiting for an image. Try any panoramic radiograph — DENTEX or Tufts both work.")
        st.stop()

    import cv2
    import numpy as np

    from scripts.run_inference import draw_overlay, run_pipeline

    file_bytes = np.frombuffer(uploaded.getvalue(), dtype=np.uint8)
    img = cv2.imdecode(file_bytes, cv2.IMREAD_COLOR)
    if img is None:
        st.error("Could not decode this file as an image.")
        st.stop()
    raw = cv2.imdecode(file_bytes, cv2.IMREAD_UNCHANGED)

    with st.spinner("Running all six stages …"), pipeline_lock():
        report = run_pipeline(img, models, device, paths, image_label=uploaded.name,
                              verbose=False, source_dtype=raw.dtype if raw is not None else None)
    for w in report["image"]["warnings"]:
        st.warning(f"Input: {w}. The results below may not hold for this image.")

    s = report["summary"]
    c1, c2, c3, c4, c5 = st.columns(5)
    c1.metric("Teeth detected", s["teeth_detected"])
    c2.metric("Assessable", s["teeth_assessable"])
    c3.metric("Distinct FDI codes", s["distinct_fdi_codes"])
    c4.metric("Caries-positive", s["caries_positive"])
    c5.metric("Stage-4 flags", s["bone_loss_positive"],
              help="Teeth near an abnormality. Not a periodontal finding — see Limitations.")
    if s["duplicate_fdi_codes"]:
        st.warning(f"{s['duplicate_fdi_codes']} duplicate FDI codes emitted — should be 0.")

    left, right = st.columns([3, 2])
    with left:
        st.subheader("Annotated overlay")
        # Drawn in memory, not written to disk (15 Oct 2026): a file per upload kept every
        # user's radiograph under outputs/_app_overlays/ for good. draw_overlay returns a BGR
        # array, hence channels="BGR".
        viz = draw_overlay(img, report)
        # width="stretch", NOT use_column_width / use_container_width. `use_column_width` was
        # REMOVED in Streamlit 1.6x and raised TypeError at runtime the first time anyone
        # actually uploaded an image to this demo (27 Aug 2026) -- the build and the page load
        # were both green, because the call is only reached after an upload. Its obvious
        # replacement `use_container_width` is ITSELF deprecated ("will be removed in a future
        # release", per st.image's docstring in 1.62), so switching to it would have fixed the
        # crash and re-armed the same trap. `width="stretch"` is the current API for both
        # st.image and st.dataframe.
        st.image(viz, channels="BGR", width="stretch",
                caption="Orange = finding (caries or Stage-4 flag) · Blue = no finding "
                        "(thin, '?' = numbering uncertain) · Grey = not assessable")

    with right:
        st.subheader("Per-tooth findings")
        rows = []
        for t in report["teeth"]:
            rows.append({
                "FDI": t["fdi"] if t["fdi"] is not None else "—",
                "Det. conf": round(t["detection_confidence"], 3),
                "FDI conf": round(t["fdi_confidence"], 3) if t["fdi_confidence"] is not None else "—",
                "Caries": t["caries"]["finding"],
                # Calibrated, not raw. The raw gate is systematically overconfident (test ECE
                # 0.136 vs 0.043 calibrated), so showing the raw number would tell a viewer a
                # borderline positive is a confident one. A `caries` verdict can legitimately
                # display a calibrated confidence below 0.5 -- that is the honest reading of a
                # gate whose precision is 0.40, not a bug. RESULTS_LOG 2026-08-27s.
                "Caries conf (cal.)": (round(t["caries"]["gate_confidence_calibrated"], 3)
                                       if t["caries"].get("gate_confidence_calibrated") is not None
                                       else "—"),
                # Not "Bone loss": Stage 4 flags proximity to an abnormality (Limitations below).
                "Stage 4 flag": "flagged" if t["bone_loss"]["finding"] == "bone_loss" else "—",
                "Assessable": "✅" if t["assessable"] else "❌",
            })
        # width="stretch" -- see the note on st.image above; use_container_width is deprecated.
        st.dataframe(rows, width="stretch", height=420, hide_index=True)

    st.subheader("⚠️ Limitations — read before trusting a number above")
    lim = report["limitations"]
    # None for a detector with no measured profile (an unregistered --detector); `:.1%` would crash.
    pct = lambda v: "not measured" if v is None else f"{v:.1%}"  # noqa: E731
    st.markdown(f"""
- **Detector recall {pct(lim['stage1_detector_recall'])}** and **Stage-2 numbering
  {pct(lim['stage2_fdi_exact_end_to_end'])} end-to-end** — {lim['interpretation']}
- **Caries**: {lim['caries_method_caveat']}
- **Caries labelling**: {lim['caries_presumed_negative_assumption']}
- **Stage 4 is not a periodontal finding**: {lim['bone_loss_label_and_validation']}
- **Stage 4 outside Tufts**: {lim['bone_loss_domain_shift']}
- **Stage-4 severity grade**: {lim['bone_severity_not_evaluated']}
- **Caries severity**: {lim['caries_severity_not_evaluated']}
""")
    st.warning(
        "This pipeline is **not clinically validated**. It composes four independently "
        "trained models; the numbers above are research measurements, not a diagnosis."
    )

    st.download_button("Download full JSON report", data=__import__("json").dumps(report, indent=2, allow_nan=False),
                       file_name=f"{Path(uploaded.name).stem}_report.json", mime="application/json")

    with st.expander("Model versions used"):
        st.json(report["models"])


if __name__ == "__main__":
    main()
