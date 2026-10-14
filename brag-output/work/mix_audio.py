#!/usr/bin/env python
"""Soundtrack: the narration placed on the shared timeline, over a quiet synthesized pad.

    python brag-output/work/mix_audio.py        # -> work/mix.wav (48 kHz stereo float)

The pad is generated here (additive synthesis, one key: C major / A minor), so nothing is
downloaded. It sits about 14 dB under the voice, ducks a further ~5 dB while anyone speaks, and
swells softly into each of the three part cards. Loudness is normalised when muxing.
"""

import json
import subprocess
from pathlib import Path

import numpy as np

WORK = Path(__file__).resolve().parent
SR = 48000


def decode(path):
    raw = subprocess.run(["ffmpeg", "-v", "error", "-i", str(path), "-f", "f32le", "-ac", "1", "-ar", str(SR), "-"],
                         capture_output=True, check=True).stdout
    return np.frombuffer(raw, np.float32).astype(np.float64)


def hz(midi):
    return 440.0 * 2 ** ((midi - 69) / 12)


def smooth(x, ms_up, ms_down):
    """One-pole envelope follower with separate attack/release."""
    a_up, a_dn = np.exp(-1 / (SR * ms_up / 1000)), np.exp(-1 / (SR * ms_down / 1000))
    y, out = 0.0, np.empty_like(x)
    for i, v in enumerate(x):
        a = a_up if v > y else a_dn
        y = a * y + (1 - a) * v
        out[i] = y
    return out


def main():
    tl = json.loads((WORK / "timeline.json").read_text())
    total = tl["total"]
    n = int((total + 0.5) * SR)
    t = np.arange(n) / SR

    # ---- narration
    voice = np.zeros(n)
    for s in tl["scenes"]:
        a = decode(WORK / "voice" / f"{s['id']}.mp3")
        i0 = int((s["start"] + s["voice_at"]) * SR)
        voice[i0:i0 + len(a)] += a[: max(0, n - i0)]
    speech = voice[np.abs(voice) > 1e-3]
    voice *= 10 ** (-19 / 20) / (np.sqrt(np.mean(speech ** 2)) + 1e-9)          # speech RMS ~ -19 dBFS

    # voice-activity envelope for ducking, computed on a 100 Hz grid then upsampled
    hop = SR // 100
    rms = np.sqrt(np.convolve(voice[: len(voice) // hop * hop].reshape(-1, hop).__pow__(2).mean(1), np.ones(5) / 5, "same"))
    act = (rms > 10 ** (-40 / 20)).astype(float)
    a_up, a_dn = np.exp(-1 / (100 * 0.12)), np.exp(-1 / (100 * 0.6))
    env, y = np.empty_like(act), 0.0
    for i, v in enumerate(act):
        a = a_up if v > y else a_dn
        y = a * y + (1 - a) * v
        env[i] = y
    duck = np.interp(t, np.arange(len(env)) * hop / SR, env)

    # ---- pad: Cmaj9 - Am9 - Fmaj7(#11-ish) - G6/9, 8 s per chord, 2.5 s crossfades
    chords = [[48, 55, 59, 62, 64], [45, 52, 55, 59, 60], [41, 48, 52, 55, 57], [43, 50, 55, 57, 62]]
    L, R = np.zeros(n), np.zeros(n)
    bar, xf = 8.0, 2.5
    k = 0
    while k * bar < total + bar:
        notes = chords[k % len(chords)]
        t0 = k * bar - xf
        i0, i1 = max(0, int(t0 * SR)), min(n, int((t0 + bar + 2 * xf) * SR))
        if i1 <= i0:
            k += 1
            continue
        tt = t[i0:i1] - t0
        w = np.clip(tt / xf, 0, 1) * np.clip((bar + 2 * xf - tt) / xf, 0, 1)
        w = np.sin(w * np.pi / 2) ** 2
        for m in notes:
            f = hz(m)
            for side, det in ((L, 0.9985), (R, 1.0015)):
                sig = np.zeros_like(tt)
                for h in range(1, 6):                                   # soft, dark timbre
                    sig += np.sin(2 * np.pi * f * det * h * tt + h * 0.7) / h ** 1.8
                side[i0:i1] += w * sig * 0.06
        bass = np.sin(2 * np.pi * hz(notes[0] - 12) * tt) * 0.10            # root, an octave down
        L[i0:i1] += w * bass
        R[i0:i1] += w * bass
        k += 1
    # slow shimmer: chord tones two octaves up, one every 2 s, long decay
    for j, ts in enumerate(np.arange(1.0, total, 2.0)):
        notes = chords[int(ts // bar) % len(chords)]
        f = hz(notes[(j * 3) % len(notes)] + 24)
        i0, i1 = int(ts * SR), min(n, int((ts + 3.5) * SR))
        tt = t[i0:i1] - ts
        tone = np.sin(2 * np.pi * f * tt) * np.exp(-tt / 1.1) * np.minimum(tt / 0.02, 1) * 0.018
        (L if j % 2 else R)[i0:i1] += tone
        (R if j % 2 else L)[i0:i1] += tone * 0.5
    # gentle breathing of the pad level
    lfo = 0.85 + 0.15 * np.sin(2 * np.pi * t / 16)
    L *= lfo
    R *= lfo

    # ---- swells into each part card (filtered noise riser + pad lift)
    rng = np.random.default_rng(7)
    for sid in ("s02_problem", "s06_input", "s14_timeline"):
        st = next(s["start"] for s in tl["scenes"] if s["id"] == sid)
        i0, i1 = int((st - 1.4) * SR), int((st + 0.6) * SR)
        tt = (np.arange(i1 - i0) / SR)
        noise = rng.standard_normal(i1 - i0)
        noise = np.convolve(noise, np.ones(24) / 24, "same")                  # soften the hiss
        shape = np.clip(tt / 1.4, 0, 1) ** 2 * np.clip((2.0 - tt) / 0.6, 0, 1)
        for side in (L, R):
            side[i0:i1] += noise * shape * 0.05

    music = np.stack([L, R])
    mus_rms = np.sqrt(np.mean(music ** 2))
    music *= 10 ** (-31 / 20) / mus_rms                                     # bed ~ -31 dBFS
    music *= 1 - 0.45 * duck                                                 # ~ -5 dB under speech
    fade = np.clip(t / 2.0, 0, 1) * np.clip((total - t) / 3.0, 0, 1)
    music *= fade

    mix = music + voice[None, :]
    peak = np.abs(mix).max()
    if peak > 0.89:
        mix *= 0.89 / peak
    out = WORK / "mix.wav"
    subprocess.run(["ffmpeg", "-y", "-v", "error", "-f", "f32le", "-ar", str(SR), "-ac", "2", "-i", "-", str(out)],
                   input=mix.T.astype(np.float32).tobytes(), check=True)
    print(f"mix -> {out}  {total:.1f} s  peak {peak:.2f}")


if __name__ == "__main__":
    main()
