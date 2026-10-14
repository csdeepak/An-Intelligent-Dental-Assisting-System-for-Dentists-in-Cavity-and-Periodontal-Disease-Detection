#!/usr/bin/env python
"""Final mux: poster as frame 0, loudness-normalised audio, captions as a selectable track.

    python brag-output/work/finalize.py [poster_time_s]     # -> brag-output/brag.mp4, brag.jpg

The poster replaces frame 0 rather than adding a frame, so the duration and A/V sync are unchanged.
"""

import subprocess
import sys
from pathlib import Path

WORK = Path(__file__).resolve().parent
OUT = WORK.parent
POSTER_T = float(sys.argv[1]) if len(sys.argv) > 1 else 7.0


def run(cmd):
    print(" ".join(map(str, cmd)))
    subprocess.run(list(map(str, cmd)), check=True)


def main():
    stills = WORK / "stills" / "poster"
    run(["node", WORK / "render.mjs", "stills", stills, POSTER_T])
    png = next(stills.glob("*.png"))
    run(["ffmpeg", "-y", "-v", "error", "-i", png, "-q:v", "2", OUT / "brag.jpg"])
    run(["ffmpeg", "-y", "-v", "error",
         "-i", WORK / "video_silent.mp4", "-loop", "1", "-t", "0.04", "-i", png, "-i", WORK / "mix.wav",
         "-i", OUT / "captions.srt",
         "-filter_complex", "[0:v][1:v]overlay=enable='eq(n,0)'[v];[2:a]loudnorm=I=-16:TP=-1.5:LRA=11,aresample=48000[a]",
         "-map", "[v]", "-map", "[a]", "-map", "3:s",
         "-c:v", "libx264", "-preset", "slow", "-crf", "17", "-pix_fmt", "yuv420p",
         "-c:a", "aac", "-b:a", "192k", "-c:s", "mov_text", "-metadata:s:s:0", "language=eng",
         "-movflags", "+faststart", "-t", "355.066", OUT / "brag.mp4"])
    run(["ffprobe", "-v", "error", "-show_entries", "format=duration,size:stream=codec_type,codec_name,width,height",
         "-of", "compact", OUT / "brag.mp4"])


if __name__ == "__main__":
    main()
