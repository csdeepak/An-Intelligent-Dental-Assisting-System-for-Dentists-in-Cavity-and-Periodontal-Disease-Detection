#!/usr/bin/env python
"""Captions (SRT) from the narration's own word timings: <= 2 lines of <= 44 characters per cue.

    python brag-output/work/make_captions.py      # -> brag-output/captions.srt
"""

import json
import re
from pathlib import Path

WORK = Path(__file__).resolve().parent
MAXC = 44


def ts(sec):
    h, rem = divmod(sec, 3600)
    m, s = divmod(rem, 60)
    return f"{int(h):02d}:{int(m):02d}:{int(s):02d},{int(round((s - int(s)) * 1000)):03d}"


def main():
    tl = json.loads((WORK / "timeline.json").read_text())
    narr = {s["id"]: s["text"] for s in json.loads((WORK / "narration.json").read_text(encoding="utf-8"))["scenes"]}
    cues = []
    for s in tl["scenes"]:
        # spoken spellings back to their written form for the captions
        text = narr[s["id"]].replace("O P G", "OPG").replace("F D I", "FDI").replace("C P U", "CPU")
        tokens = text.split()
        words = s["words"]
        # align caption tokens to timed words by order; spelled-out letters were merged above
        times, wi = [], 0
        for tok in tokens:
            times.append(s["start"] + words[min(wi, len(words) - 1)]["t"])
            span = 3 if tok.strip(",.?:") in ("OPG", "FDI", "CPU") else 1
            wi += span
        chunk, c0 = [], None
        for i, tok in enumerate(tokens):
            if c0 is None:
                c0 = times[i]
            chunk.append(tok)
            line = " ".join(chunk)
            end_sentence = re.search(r"[.?:]$", tok)
            if len(line) > 2 * MAXC - 10 or end_sentence or i == len(tokens) - 1:
                t1 = times[i + 1] if i + 1 < len(tokens) else s["start"] + s["voice_at"] + s["spoken"]
                cues.append((c0, max(t1, c0 + 1.0), line))
                chunk, c0 = [], None
    out = []
    for k, (a, b, line) in enumerate(cues, 1):
        if len(line) > MAXC:                                   # break into two balanced lines
            words = line.split()
            best = min(range(1, len(words)), key=lambda j: abs(len(" ".join(words[:j])) - len(" ".join(words[j:]))))
            line = " ".join(words[:best]) + "\n" + " ".join(words[best:])
        out.append(f"{k}\n{ts(a)} --> {ts(b - 0.05)}\n{line}\n")
    (WORK.parent / "captions.srt").write_text("\n".join(out), encoding="utf-8")
    print(f"{len(cues)} cues -> {WORK.parent / 'captions.srt'}")


if __name__ == "__main__":
    main()
