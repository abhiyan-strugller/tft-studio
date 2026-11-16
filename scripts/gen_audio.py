#!/usr/bin/env python3
"""ORIGINAL procedural audio bed for TempleFront reels — never licensed music,
so a reel can never draw a copyright claim.

A warm tanpura-style drone (root, fifth, octave with slow beating), a soft
heartbeat pulse, and a singing-bowl strike (inharmonic partials, long decay)
on every slide cut. Deterministic per seed so a reel's audio is reproducible;
the seed varies root and tempo so reels don't all sound the same.

  python3 scripts/gen_audio.py --seconds 24 --out bed.wav --seed 3 --cuts 3.5,7,10.5
"""
import argparse
import wave

import numpy as np

SR = 44100
ROOTS = [110.0, 116.54, 123.47, 98.0, 103.83]  # A2, A#2, B2, G2, G#2


def bowl(n, f0, rng):
    t = np.arange(n) / SR
    ratios = [1.0, 2.71, 5.15, 8.17]
    out = np.zeros(n)
    for k, r in enumerate(ratios):
        det = 1 + rng.uniform(-0.002, 0.002)
        amp = 0.5 / (k + 1) ** 1.2
        dec = 2.8 / (1 + k * 0.9)
        beat = 1 + 0.25 * np.sin(2 * np.pi * (0.8 + k * 0.4) * t)
        out += amp * np.sin(2 * np.pi * f0 * r * det * t) * np.exp(-t / dec) * beat
    att = np.minimum(1, t / 0.004)
    return out * att


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--seconds", type=float, required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--seed", type=int, default=1)
    ap.add_argument("--cuts", default="")
    a = ap.parse_args()
    rng = np.random.default_rng(a.seed)
    n = int(a.seconds * SR)
    t = np.arange(n) / SR
    root = ROOTS[a.seed % len(ROOTS)]

    # drone: tanpura-ish pluck cycle on Pa-Sa-Sa-Sa (fifth, octave, octave, root)
    drone = np.zeros(n)
    for f, amp in [(root, 0.22), (root * 1.5, 0.12), (root * 2, 0.10), (root * 2.0 * 1.003, 0.06)]:
        drone += amp * np.sin(2 * np.pi * f * t + rng.uniform(0, 6.28))
        drone += amp * 0.35 * np.sin(2 * np.pi * f * 2 * t)
    swell = 0.75 + 0.25 * np.sin(2 * np.pi * t / 6.0)
    drone *= swell

    # soft pulse
    bpm = 64 + (a.seed * 7) % 18
    beat = 60.0 / bpm
    pulse = np.zeros(n)
    hit = int(0.35 * SR)
    th = np.arange(hit) / SR
    kick = np.sin(2 * np.pi * (55 * np.exp(-th * 8) + 38) * th) * np.exp(-th * 9)
    k = 0.0
    while k < a.seconds:
        i = int(k * SR)
        j = min(n, i + hit)
        pulse[i:j] += 0.30 * kick[: j - i]
        k += beat

    # bowl strikes on cuts and at the start
    bowls = np.zeros(n)
    cuts = [0.05] + [float(c) for c in a.cuts.split(",") if c.strip()]
    for c in cuts:
        i = int(c * SR)
        if i >= n:
            continue
        L = min(n - i, int(6 * SR))
        bowls[i:i + L] += 0.33 * bowl(L, root * 4 * rng.choice([1.0, 1.122, 1.335]), rng)

    mix = drone + pulse + bowls
    fade = int(1.2 * SR)
    env = np.ones(n)
    env[: int(0.6 * SR)] = np.linspace(0, 1, int(0.6 * SR))
    env[-fade:] = np.linspace(1, 0, fade)
    mix *= env
    mix = np.tanh(mix * 1.4) * 0.8
    stereo = np.stack([mix, np.roll(mix, int(0.012 * SR))], axis=1)
    pcm = (stereo * 32767 * 0.9).astype(np.int16)
    with wave.open(a.out, "wb") as w:
        w.setnchannels(2)
        w.setsampwidth(2)
        w.setframerate(SR)
        w.writeframes(pcm.tobytes())


if __name__ == "__main__":
    main()
