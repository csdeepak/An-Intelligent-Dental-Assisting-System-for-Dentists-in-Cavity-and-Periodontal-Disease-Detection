"""
The positional-assignment ceiling, computed reproducibly.

WHY THIS FILE EXISTS
--------------------
The ceiling figure quoted throughout the Stage-2 write-up was originally produced by an
ad-hoc snippet that was never saved. It then reached four documents as **67.0%**, which is
wrong twice over:

  1. **67.0% is the detector's recall**, not the ceiling. The two are unrelated quantities
     that happened to be confused while writing up RESULTS_LOG 2026-08-22j. The real ceiling
     on the clean 164-image set is **66.3%** (67/101).
  2. The "+2.4 points" margin compared the positional ceiling — restricted to teeth in
     COMPLETE (8-detection) quadrants — against the head's accuracy over ALL detected teeth.
     Different populations. On the *same* population the margin is **+13.9 points**.

An unreproducible number is how that survived. This script reads only saved run artefacts,
recomputes both methods over identical rows, and writes JSON, so the figure can be checked
rather than remembered.

DEFINITION
----------
"Detections in quadrant" counts the DETECTOR's boxes falling in a tooth's own quadrant
(`per_quadrant` in the per-image artefact), matching RESULTS_LOG 2026-08-22f. Bucketing uses
the POSITIONAL run's counts for both methods so the populations are identical and the
comparison is like-for-like.

Usage:
    python scripts/eval/analyze_stage2_ceiling.py
    python scripts/eval/analyze_stage2_ceiling.py --run outputs/stage2_clean
"""

import argparse
import json
from collections import defaultdict
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
DEF_RUN = REPO_ROOT / "outputs/stage2_clean"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--run", type=Path, default=DEF_RUN)
    ap.add_argument("--out", type=Path, default=None)
    args = ap.parse_args()
    out = args.out or (args.run / "stage2_ceiling_analysis.json")

    rp = json.loads((args.run / "stage2_rows_positional.json").read_text())
    rh = json.loads((args.run / "stage2_rows_head.json").read_text())
    per = json.loads((args.run / "stage2_per_image_positional.json").read_text())
    pq = {p["image"]: p["per_quadrant"] for p in per}

    kp = {(r["image"], r["gt_fdi"]): r for r in rp}
    kh = {(r["image"], r["gt_fdi"]): r for r in rh}
    if set(kp) != set(kh):
        raise SystemExit("row sets differ between methods — not a like-for-like comparison")
    if any(kp[k]["detected"] != kh[k]["detected"] for k in kp):
        raise SystemExit("detection differs between methods — bucketing would not be shared")

    buckets = defaultdict(lambda: {"n": 0, "positional": 0, "head": 0})
    for k, r in kp.items():
        if not r["detected"]:
            continue
        b = buckets[pq[r["image"]].get(str(r["gt_fdi"] // 10), 0)]
        b["n"] += 1
        b["positional"] += int(r["pred_fdi"] == r["gt_fdi"])
        b["head"] += int(kh[k]["pred_fdi"] == kh[k]["gt_fdi"])

    table = []
    for d, b in sorted(buckets.items()):
        table.append({"detections_in_quadrant": d, "n": b["n"],
                      "positional_exact": b["positional"] / b["n"],
                      "head_exact": b["head"] / b["n"],
                      "delta": (b["head"] - b["positional"]) / b["n"]})

    c = buckets.get(8)
    if not c:
        raise SystemExit("no complete (8-detection) quadrants in this run")
    res = {
        "run": str(args.run),
        "definition": "bucketed by DETECTOR boxes in the tooth's own quadrant; "
                      "buckets taken from the positional run so both methods share a population",
        "n_detected_teeth": sum(b["n"] for b in buckets.values()),
        "by_bucket": table,
        "complete_quadrant_ceiling": {
            "n": c["n"],
            "positional_exact": c["positional"] / c["n"],
            "head_exact": c["head"] / c["n"],
            "margin": (c["head"] - c["positional"]) / c["n"],
        },
        "supersedes": "the 67.0% ceiling and +2.4 point margin in RESULTS_LOG 2026-08-22j",
    }
    out.write_text(json.dumps(res, indent=2) + "\n")

    print(f"{'dets':>5} {'n':>5} {'positional':>11} {'head':>8} {'delta':>8}")
    for r in table:
        print(f"{r['detections_in_quadrant']:>5} {r['n']:>5} "
              f"{r['positional_exact']:>10.1%} {r['head_exact']:>8.1%} {r['delta']:>+8.1%}")
    cc = res["complete_quadrant_ceiling"]
    print(f"\nCOMPLETE (8-detection) quadrants, n={cc['n']}:")
    print(f"  positional ceiling {cc['positional_exact']:.1%}   "
          f"head {cc['head_exact']:.1%}   margin {cc['margin']*100:+.1f} points")
    print(f"\nwrote {out}")


if __name__ == "__main__":
    main()
