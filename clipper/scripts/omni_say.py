#!/usr/bin/env python3
"""omni_say.py - Hindi (or any of 600+ languages) voice-over with OmniVoice (k2-fsa/OmniVoice, Apache-2.0).

Tested 23 Nov 2026 on Ankush's MacBook Air (8 GB, MPS, fp16): model load ~5 min the first time
(3.3 GB download), then ~55 s to make ~16 s of Hindi speech. Faster, storyteller pace vs Edge Madhur
(same script: 15.8 s vs 26 s). VoxCPM2 (42.9K stars) was also tried: on MPS it needs float32
(~8 GB RAM, too much for this Mac) and on CPU it ran at ~5 s per step (about an hour per Short).

Setup (once, on the Mac):
  /opt/homebrew/bin/python3.12 -m venv ~/faceless-shorts/voice-test/omni-venv
  ~/faceless-shorts/voice-test/omni-venv/bin/pip install torch==2.8.0 torchaudio==2.8.0 omnivoice soundfile

Usage:
  PY=~/faceless-shorts/voice-test/omni-venv/bin/python
  $PY omni_say.py lines.txt out_dir [--instruct "male, young adult, moderate pitch"] [--ref me.wav --ref-text "..."]
      [--speed 1.0] [--device mps|cpu]
  One line of lines.txt -> out_dir/l<N>.wav (24 kHz). Same file layout as the Edge build.sh (l1, l2, ...),
  so build.sh can swap Edge for this with one line.

Voice rules (channel):
  - --instruct designs a NEW synthetic voice (gender, age, pitch). Keep the same instruct for every line
    of a video, and the same one across videos so the channel has one recognisable voice.
  - --ref clones a voice from 3-10 s of audio. ONLY use Ankush's own recording (or a voice he has the
    rights to). Never clone a streamer, another page's narrator or any real person without consent.
  - Write numbers as words; Devanagari text in, no tags.
"""
import argparse, os, sys, time


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("lines")
    ap.add_argument("out_dir")
    ap.add_argument("--instruct", default="male, young adult, moderate pitch")
    ap.add_argument("--ref")
    ap.add_argument("--ref-text")
    ap.add_argument("--speed", type=float, default=None)
    ap.add_argument("--device", default="mps")
    a = ap.parse_args()

    import torch, soundfile as sf
    from omnivoice import OmniVoice

    os.makedirs(a.out_dir, exist_ok=True)
    lines = [l.strip() for l in open(a.lines, encoding="utf-8") if l.strip()]
    t0 = time.time()
    model = OmniVoice.from_pretrained("k2-fsa/OmniVoice", device_map=a.device,
                                      dtype=torch.float32 if a.device == "cpu" else torch.float16)
    print(f"loaded on {a.device} in {time.time() - t0:.0f} s", flush=True)

    kw = {}
    if a.ref:
        kw["voice_clone_prompt"] = model.create_voice_clone_prompt(ref_audio=a.ref, ref_text=a.ref_text)
    else:
        kw["instruct"] = a.instruct
    if a.speed:
        kw["speed"] = a.speed
    for i, line in enumerate(lines, 1):
        t = time.time()
        try:
            audio = model.generate(text=line, **kw)
        except TypeError:          # older omnivoice without speed=
            kw.pop("speed", None)
            audio = model.generate(text=line, **kw)
        out = os.path.join(a.out_dir, f"l{i}.wav")
        sf.write(out, audio[0], 24000)
        print(f"l{i}: {len(audio[0]) / 24000:.1f} s audio in {time.time() - t:.0f} s", flush=True)


if __name__ == "__main__":
    sys.exit(main())
