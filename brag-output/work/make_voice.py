#!/usr/bin/env python
"""Synthesize the narration scene by scene with edge-tts, keep word timings, build the timeline.

    python brag-output/work/make_voice.py            # voice/<id>.mp3, voice/<id>.words.json, timeline.json

Scene duration = LEAD + spoken length + TAIL, never below the scene's `min`. timeline.json is
what the composition (site/data.js) and the audio mix both read, so picture and sound share one
clock.
"""

import asyncio
import json
import subprocess
from pathlib import Path

import edge_tts

WORK = Path(__file__).resolve().parent
VOICE = WORK / "voice"
LEAD, TAIL = 0.45, 0.80          # seconds of picture before the first word / after the last


async def synth(scene, voice, rate):
    mp3, words = VOICE / f"{scene['id']}.mp3", VOICE / f"{scene['id']}.words.json"
    if mp3.exists() and words.exists() and json.loads(words.read_text()).get("key") == [scene["text"], voice, rate]:
        return
    com = edge_tts.Communicate(scene["text"], voice, rate=rate, boundary="WordBoundary")
    audio, marks = bytearray(), []
    async for chunk in com.stream():
        if chunk["type"] == "audio":
            audio += chunk["data"]
        elif chunk["type"] == "WordBoundary":
            marks.append({"w": chunk["text"], "t": chunk["offset"] / 1e7,
                          "d": chunk["duration"] / 1e7})
    mp3.write_bytes(bytes(audio))
    words.write_text(json.dumps({"key": [scene["text"], voice, rate], "words": marks}, indent=1))


def duration(path):
    out = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration",
                          "-of", "default=nw=1:nk=1", str(path)], capture_output=True, text=True)
    return float(out.stdout.strip())


def main():
    cfg = json.loads((WORK / "narration.json").read_text(encoding="utf-8"))
    VOICE.mkdir(exist_ok=True)
    for s in cfg["scenes"]:
        asyncio.run(synth(s, cfg["voice"], cfg["rate"]))
    t, scenes = 0.0, []
    for s in cfg["scenes"]:
        spoken = duration(VOICE / f"{s['id']}.mp3")
        dur = max(s["min"], LEAD + spoken + TAIL)
        words = json.loads((VOICE / f"{s['id']}.words.json").read_text())["words"]
        scenes.append({"id": s["id"], "part": s["part"], "start": round(t, 3),
                       "dur": round(dur, 3), "voice_at": LEAD, "spoken": round(spoken, 3),
                       "words": [{"w": w["w"], "t": round(LEAD + w["t"], 3)} for w in words]})
        t += dur
    (WORK / "timeline.json").write_text(json.dumps({"fps": 30, "total": round(t, 3),
                                                    "scenes": scenes}, indent=1))
    for s in scenes:
        print(f"{s['id']:16s} start {s['start']:7.2f}  dur {s['dur']:6.2f}  spoken {s['spoken']:6.2f}")
    print(f"total {t:.1f} s ({t / 60:.2f} min)")


if __name__ == "__main__":
    main()
