#!/usr/bin/env python
"""
Fetch the DENTEX subsets this repo actually uses, from the project Google Drive.

WHY THIS IS SELECTIVE, NOT `gdown --folder` ON THE ROOT
--------------------------------------------------------
The drive holds 10,781 entries (~13 GB). `data/README.md` records that two of the image
subsets are **unused** by anything in this repo -- `training_data/quadrant/xrays` (693) and
`training_data/unlabelled/xrays` (1,571) -- and two more directories under
`quadrant-enumeration-disease/` (`processed_dataset`, 3,711 files; `severity_data`, 2,900) are
*derived* crops this repo rebuilds from source with `build_dentex_crops.py`. Fetching those
would cost bandwidth and disk for data no script reads.

What this DOES fetch (1,390 images + 3 annotation files):

  training_data/quadrant-enumeration-disease/xrays   705  the caries cascade source (T0.2-T0.4)
  training_data/quadrant_enumeration/xrays           634  trains the Stage-2 enumeration head
  validation_data/quadrant_enumeration_disease/xrays  51  extern50, an independent second eval

`disease/` (250 images) is deliberately skipped -- it was fetched on 27 Aug and is already
local. Re-run this script any time; it skips whatever is already present and verified.

INTEGRITY IS CHECKED, NOT ASSUMED
----------------------------------
Every PNG is opened and every JSON parsed after download. On 27 Aug an image left truncated at
2,428 bytes by an interrupted download passed a `size > 0` check and silently cost an
evaluation run (`RESULTS_LOG.md` 2026-08-27e). A size check is not an integrity check, so a
file that fails verification is deleted and retried rather than left on disk looking fine.

Usage:
    python scripts/dentex/fetch_dentex_subsets.py                # fetch everything missing
    python scripts/dentex/fetch_dentex_subsets.py --verify-only  # check what is already there
"""

import argparse
import json
import sys
import time
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]

DRIVE_FOLDER = "https://drive.google.com/drive/folders/1DtdE_TYuYTeyvuaveQEvuhSpwL6U8Ovp"
DEF_DEST = Path.home() / "Downloads" / "Capstone" / "DENTEX"
RAW_DIR = REPO_ROOT / "data" / "dentex" / "raw"

# Drive-path prefixes to fetch. Anything not matching one of these is skipped.
WANTED_PREFIXES = (
    "training_data/quadrant-enumeration-disease/xrays/",
    "training_data/quadrant_enumeration/xrays/",
    "validation_data/quadrant_enumeration_disease/xrays/",
)

# Annotation files -> where the code expects them (build_dentex_crops.py's DEF_* constants).
WANTED_JSON = {
    "training_data/quadrant-enumeration-disease/train_quadrant_enumeration_disease.json":
        "train_quadrant_enumeration_disease.json",
    "training_data/quadrant_enumeration/train_quadrant_enumeration.json":
        "train_quadrant_enumeration.json",
    "validation_data/quadrant_enumeration_disease/validation_triple.json":
        "validation_triple.json",
}


def norm(p):
    return p.replace("\\", "/")


def verify(path):
    """True only if the file is genuinely readable -- not merely non-empty."""
    try:
        if path.stat().st_size == 0:
            return False
        if path.suffix.lower() == ".json":
            json.loads(path.read_text(encoding="utf-8"))
            return True
        from PIL import Image
        with Image.open(path) as im:
            im.verify()          # catches truncation, which a size check does not
        return True
    except Exception:
        return False


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dest", type=Path, default=DEF_DEST)
    ap.add_argument("--verify-only", action="store_true")
    ap.add_argument("--limit", type=int, default=None, help="stop after N downloads (smoke test)")
    args = ap.parse_args()

    import gdown            # listing only; downloads use requests (see below)

    print(f"listing {DRIVE_FOLDER} …", flush=True)
    entries = gdown.download_folder(url=DRIVE_FOLDER, skip_download=True, quiet=True)
    print(f"  {len(entries)} entries on the drive", flush=True)

    jobs = []   # (drive_path, file_id, local_path)
    for e in entries:
        p = norm(e.path)
        if p in WANTED_JSON:
            jobs.append((p, e.id, RAW_DIR / WANTED_JSON[p]))
        elif p.startswith(WANTED_PREFIXES):
            jobs.append((p, e.id, args.dest / p))

    print(f"  {len(jobs)} files wanted "
          f"({len(WANTED_JSON)} annotations + {len(jobs) - len(WANTED_JSON)} images)", flush=True)

    present = [j for j in jobs if j[2].exists() and verify(j[2])]
    stale = [j for j in jobs if j[2].exists() and not verify(j[2])]
    todo = [j for j in jobs if not j[2].exists()] + stale

    print(f"  already present and verified: {len(present)}")
    if stale:
        print(f"  present but CORRUPT (will re-fetch): {len(stale)}")
    print(f"  to download: {len(todo)}", flush=True)

    if args.verify_only:
        return 0 if not stale else 1

    if args.limit:
        todo = todo[:args.limit]

    # ONE session for all files, and a few workers. Measured on this drive: gdown's
    # per-file download re-establishes a session each time and ran at **45.7 s/file**
    # (~90 KB/s for 4 MB images) while the same drive served a single 45 MB checkpoint at
    # 29 MB/s -- i.e. the cost was request setup, not bandwidth. A persistent
    # requests.Session against the direct download endpoint measured **3.31 s/file**, a 14x
    # improvement, which is the difference between ~17 hours and ~30 minutes for 1,390 files.
    # Workers kept low on purpose: Drive rate-limits, and a concurrent probe during an
    # earlier run triggered "Failed to retrieve file url" on an unrelated file.
    import threading

    import requests

    lock = threading.Lock()
    counts = {"ok": 0, "failed": 0, "done": 0}
    local_sessions = threading.local()

    def session():
        s = getattr(local_sessions, "s", None)
        if s is None:
            s = local_sessions.s = requests.Session()
        return s

    def fetch_one(job):
        dpath, fid, local = job
        local.parent.mkdir(parents=True, exist_ok=True)
        tmp = local.with_suffix(local.suffix + ".part")
        for attempt in (1, 2, 3, 4):
            try:
                r = session().get(
                    "https://drive.usercontent.google.com/download",
                    params={"id": fid, "export": "download", "confirm": "t"},
                    timeout=180,
                )
                r.raise_for_status()
                tmp.write_bytes(r.content)
                # Write to .part and only rename once verified, so an interrupted run can
                # never leave a truncated file that looks complete to the next run.
                if verify(tmp):
                    tmp.replace(local)
                    with lock:
                        counts["ok"] += 1
                    return
                tmp.unlink(missing_ok=True)
            except Exception as exc:
                tmp.unlink(missing_ok=True)
                if attempt == 4:
                    with lock:
                        print(f"  FAILED {dpath}: {exc}", flush=True)
            time.sleep(2.0 * attempt)          # back off; Drive throttles
        with lock:
            counts["failed"] += 1

    def wrapped(job):
        fetch_one(job)
        with lock:
            counts["done"] += 1
            d = counts["done"]
            if d % 50 == 0 or d == len(todo):
                print(f"  {d}/{len(todo)}  ok={counts['ok']} failed={counts['failed']}",
                      flush=True)

    from concurrent.futures import ThreadPoolExecutor
    with ThreadPoolExecutor(max_workers=4) as ex:
        list(ex.map(wrapped, todo))
    ok, failed = counts["ok"], counts["failed"]

    print(f"\ndone: {ok} downloaded and verified, {failed} failed", flush=True)
    for pref in WANTED_PREFIXES:
        d = args.dest / pref
        n = len(list(d.glob("*"))) if d.exists() else 0
        print(f"  {pref:52s} {n} files")
    print(f"  {'data/dentex/raw/':52s} "
          f"{len(list(RAW_DIR.glob('*.json'))) if RAW_DIR.exists() else 0} annotations")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
