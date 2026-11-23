#!/usr/bin/env python3
"""music.py - original royalty-free synthwave bed, made in code (no samples, no copyrighted music).

  python3 music.py out.wav [--seconds 240] [--bpm 96] [--seed 7]

Am - F - C - G pads, eighth-note bass, soft four-on-the-floor kick, snare on 2 and 4, off-beat hats.
Meant to sit quietly (about -20 dB) under narration and title cards, never over streamer audio.
Needs numpy + soundfile (the omni-venv on the Mac has both).
"""
import argparse
import numpy as np
import soundfile as sf

SR = 44100


def note(n):  # MIDI -> Hz
    return 440.0 * 2 ** ((n - 69) / 12)


def saw(f, t):
    return 2 * ((f * t) % 1.0) - 1


def lowpass(x, a):
    y = np.empty_like(x)
    acc = 0.0
    for i in range(len(x)):  # small loop, fine for a 20 s loop
        acc += a * (x[i] - acc)
        y[i] = acc
    return y


def env(n, att, rel):
    e = np.ones(n)
    a, r = int(att * SR), int(rel * SR)
    e[:a] = np.linspace(0, 1, a)
    e[-r:] = np.linspace(1, 0, r)
    return e


def build_loop(bpm, rng):
    beat = 60 / bpm
    bar = 4 * beat
    chords = [[57, 60, 64], [53, 57, 60], [48, 52, 55], [55, 59, 62]]  # Am F C G
    roots = [45, 41, 36, 43]
    n = int(8 * bar * SR)
    out = np.zeros(n)
    t_all = np.arange(n) / SR
    # pads: 2 bars per chord
    for ci, ch in enumerate(chords):
        s0 = int(ci * 2 * bar * SR)
        seg = int(2 * bar * SR)
        t = np.arange(seg) / SR
        pad = np.zeros(seg)
        for m in ch:
            for det in (-0.004, 0.0, 0.004):
                pad += saw(note(m) * (1 + det), t + rng.random())
        pad = lowpass(pad / 9, 0.06) * env(seg, 0.4, 0.5)
        out[s0:s0 + seg] += 0.30 * pad
        # bass: eighth notes
        for k in range(16):
            b0 = s0 + int(k * beat / 2 * SR)
            bl = int(beat / 2 * SR * 0.9)
            tb = np.arange(bl) / SR
            f = note(roots[ci] - 12 + (12 if k % 4 == 3 else 0))
            tone = np.sin(2 * np.pi * f * tb) + 0.3 * np.sign(np.sin(2 * np.pi * f * tb))
            out[b0:b0 + bl] += 0.16 * tone * np.exp(-tb * 6)
    # drums
    nb = int(8 * 4)
    for k in range(nb):
        b0 = int(k * beat * SR)
        kl = int(0.3 * SR)
        tk = np.arange(kl) / SR
        f = 45 + 75 * np.exp(-tk * 30)
        kick = np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-tk * 9)
        out[b0:b0 + kl] += 0.45 * kick[: max(0, min(kl, n - b0))]
        if k % 2 == 1:
            sl = int(0.18 * SR)
            ns = rng.standard_normal(sl)
            ns = ns - lowpass(ns, 0.08)
            out[b0:b0 + sl] += 0.12 * ns * np.exp(-np.arange(sl) / SR * 18)
        h0 = b0 + int(beat / 2 * SR)
        hl = int(0.04 * SR)
        if h0 + hl < n:
            hs = rng.standard_normal(hl)
            hs = hs - lowpass(hs, 0.3)
            out[h0:h0 + hl] += 0.05 * hs * np.exp(-np.arange(hl) / SR * 80)
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("out")
    ap.add_argument("--seconds", type=float, default=240)
    ap.add_argument("--bpm", type=float, default=96)
    ap.add_argument("--seed", type=int, default=7)
    a = ap.parse_args()
    loop = build_loop(a.bpm, np.random.default_rng(a.seed))
    reps = int(np.ceil(a.seconds * SR / len(loop)))
    x = np.tile(loop, reps)[: int(a.seconds * SR)]
    x = x / (np.abs(x).max() + 1e-9) * 0.8
    fade = int(2 * SR)
    x[-fade:] *= np.linspace(1, 0, fade)
    sf.write(a.out, np.stack([x, x], axis=1), SR)
    print(f"wrote {a.out} ({a.seconds:.0f} s, {a.bpm:.0f} bpm)")


if __name__ == "__main__":
    main()
