#!/usr/bin/env python3
"""transcribe.py - word-timed transcript of a streamer clip for word-by-word captions.

    <whisper-venv>/bin/python transcribe.py source.mp4 [--model small.en] [--min-prob 0.6] [--start S --end E]

Writes <source>.words.json: [{"w": "airport.", "s": 10.32, "e": 10.81, "p": 0.97}, ...] in SOURCE seconds,
plus <source>.words.txt (the plain text, one segment per line, low-confidence words in [brackets]) to proofread.

Words whose probability is below --min-prob are kept in the .txt in [brackets] but marked "drop": true in the
JSON, so clip.py leaves them out: we never put words in a streamer's mouth that we are not sure of.
Needs faster-whisper (pip install faster-whisper). First run downloads the model (small.en about 480 MB).
Speech from NPCs and game dialogue is transcribed too - read the .txt against the video and delete those.
"""
import argparse, json, sys
from pathlib import Path


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("src")
    ap.add_argument("--model", default="small.en")
    ap.add_argument("--min-prob", type=float, default=0.6)
    ap.add_argument("--start", type=float, default=0.0)
    ap.add_argument("--end", type=float, default=1e9)
    a = ap.parse_args()
    from faster_whisper import WhisperModel
    model = WhisperModel(a.model, device="cpu", compute_type="int8")
    segs, info = model.transcribe(a.src, word_timestamps=True, vad_filter=True, beam_size=5,
                                  condition_on_previous_text=False)
    words, lines = [], []
    for seg in segs:
        line = []
        for w in seg.words or []:
            if w.end < a.start or w.start > a.end:
                continue
            t = w.word.strip()
            if not t:
                continue
            drop = w.probability < a.min_prob
            words.append({"w": t, "s": round(w.start, 2), "e": round(w.end, 2), "p": round(w.probability, 2),
                          **({"drop": True} if drop else {})})
            line.append(f"[{t}]" if drop else t)
        if line:
            lines.append(f"{seg.start:6.2f}-{seg.end:6.2f}  " + " ".join(line))
    out = Path(a.src).with_suffix(".words.json")
    out.write_text(json.dumps(words, indent=0))
    Path(a.src).with_suffix(".words.txt").write_text("\n".join(lines) + "\n")
    kept = sum(1 for w in words if not w.get("drop"))
    print(f"wrote {out} ({kept} words kept, {len(words) - kept} low-confidence dropped)")
    print("\n".join(lines))


if __name__ == "__main__":
    main()
