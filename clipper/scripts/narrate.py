#!/usr/bin/env python3
"""narrate.py - "Hindi storyteller" reel on top of a clip.py render (the Instagram narrated-reel look).

  python3 narrate.py narr.json [--draft]

A narrator (OmniVoice, made with omni_say.py) tells the story; the game/streamer audio is ducked under the
voice and comes back at full volume for the streamer's own big lines. Word-by-word Hinglish captions
(white caps, one yellow word) and a small coloured label chip above them, like the reference reel.

narr.json (paths relative to the json):
  base       the clip.py render (stack layout, NO captions/title card), e.g. "renders/NARR-base.mp4"
  out        output mp4
  duck       game-audio level under the narrator (default 0.15)
  cap_y      caption top as a share of height (default 0.66); chip sits just above it
  beats      list, in order:
    {"src": 24.5, "vo": "narr/l1.wav", "cap": "IShowSpeed ne GTA 6 mein asli UFO dhoondh liya", "chip": "UFO EASTER EGG",
     "hl": ["UFO"]}                     narrator line; starts where source second `src` lands in the render
    {"src_a": 47.6, "src_b": 53.9, "words": "x.captions.json", "chip": "SPEED, LIVE", "hl": ["alien"]}
                                         streamer moment: full game audio, captions from the streamer's own words
  Caption text is Latin (Hinglish) even when the voice reads Devanagari; timings are spread over the line by
  word length, 3 words per chunk. Times come from <base>.timeline.json.
"""
import json, subprocess, sys, tempfile, shutil
from pathlib import Path
from PIL import Image, ImageDraw

sys.path.insert(0, str(Path(__file__).parent))
import clip  # noqa: E402

CHIP_COL = [(255, 214, 10), (255, 60, 170), (60, 230, 255), (80, 255, 140)]


def dur(p):
    r = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", str(p)],
                       capture_output=True, text=True)
    return float(r.stdout.strip())


def spread(text, t0, length):
    """Latin caption words with timings spread by character length."""
    toks = text.split()
    w = [max(2, len(t.strip(".,!?\"'"))) + 1 for t in toks]
    tot, t, out = sum(w), t0, []
    for tok, wi in zip(toks, w):
        d = length * wi / tot
        out.append({"w": tok, "s": t, "e": t + d * 0.92})
        t += d
    return out


def chip_png(path, W, H, text, y, col):
    k = W / 1080
    img = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    f = clip.sans_font(int(38 * k), 800)
    tw = d.textlength(text.upper(), font=f)
    px, py = int(22 * k), int(10 * k)
    bw, bh = int(tw + 2 * px), int(38 * k * 1.25 + 2 * py)
    x0 = (W - bw) // 2
    d.rounded_rectangle([x0, y, x0 + bw, y + bh], radius=int(12 * k), fill=(20, 12, 40, 235))
    d.text((x0 + px, y + py), text.upper(), font=f, fill=col + (255,))
    img.save(path)


def main():
    spec_p = Path(sys.argv[1]).resolve()
    base_dir = spec_p.parent
    spec = json.loads(spec_p.read_text(encoding="utf-8"))
    base = base_dir / spec["base"]
    tl = json.loads(Path(str(base) + ".timeline.json").read_text())
    segs, total = tl["segments"], tl["total"]
    for s in segs:
        s.setdefault("speed", 1.0)
    probe = subprocess.run(["ffprobe", "-v", "error", "-select_streams", "v:0", "-show_entries",
                            "stream=width,height,r_frame_rate", "-of", "csv=p=0", str(base)],
                           capture_output=True, text=True).stdout.strip().split(",")
    W, H = int(probe[0]), int(probe[1])
    fps = probe[2]
    duck = spec.get("duck", 0.15)
    cap_y = spec.get("cap_y", 0.66)
    k = W / 1080
    chip_y = int(H * cap_y) - int(78 * k)

    tmp = Path(tempfile.mkdtemp(prefix="narr_"))
    try:
        overlays, vo_inputs, vo_ranges, words_all, n_chip = [], [], [], [], 0
        for b in spec["beats"]:
            if "vo" in b:
                o = clip.map_t(segs, b["src"])
                if o is None:
                    sys.exit(f"narrate.py: src {b['src']} is not inside the keep ranges")
                L = dur(base_dir / b["vo"])
                if o + L > total + 0.05:
                    print(f"warning: line '{b['cap'][:30]}' runs {o + L - total:.1f} s past the end")
                vo_inputs.append((base_dir / b["vo"], o))
                vo_ranges.append((o, o + L))
                ws = spread(b["cap"], o, L)
                a0, a1 = o, o + L
            else:
                ws = []
                src_words = json.loads((base_dir / b["words"]).read_text())
                for w in src_words:
                    if w.get("drop") or not (b["src_a"] <= w["s"] < b["src_b"]):
                        continue
                    o0, o1 = clip.map_t(segs, w["s"]), clip.map_t(segs, min(w["e"], b["src_b"]), end=True)
                    if o0 is not None and o1 is not None:
                        ws.append({"w": w["w"], "s": o0, "e": max(o1, o0 + 0.1)})
                a0 = clip.map_t(segs, b["src_a"]) or 0
                a1 = clip.map_t(segs, b["src_b"], end=True) or total
            hl = {h.lower() for h in b.get("hl", [])}
            for i, (c0, c1, ch) in enumerate(clip.caption_chunks(ws, 3)):
                p = str(tmp / f"cap{len(overlays)}.png")
                clip.caption_png(p, W, H, ch, hl, cap_y)
                overlays.append((p, c0, min(c1, a1 + 0.3)))
            if b.get("chip"):
                p = str(tmp / f"chip{n_chip}.png")
                chip_png(p, W, H, b["chip"], chip_y, CHIP_COL[n_chip % len(CHIP_COL)])
                overlays.append((p, a0, a1))
                n_chip += 1

        inputs, chains, last = ["-i", str(base)], [], "[0:v]"
        for i, (p, a, b2) in enumerate(overlays):
            inputs += ["-i", p]
            chains.append(f"{last}[{i + 1}:v]overlay=0:0:enable='between(t,{a:.3f},{b2:.3f})'[v{i}]")
            last = f"[v{i}]"
        n = len(overlays) + 1
        # duck the game audio while the narrator talks (short fades)
        cond = "+".join(f"between(t,{a - 0.15:.3f},{b2 + 0.15:.3f})" for a, b2 in vo_ranges) or "0"
        chains.append(f"[0:a]volume='if({cond},{duck},1)':eval=frame[ga]")
        mix = ["[ga]"]
        for j, (p, o) in enumerate(vo_inputs):
            inputs += ["-i", str(p)]
            ms = int(o * 1000)
            chains.append(f"[{n + j}:a]aresample=48000,aformat=channel_layouts=stereo,adelay={ms}|{ms},volume=1.6[vo{j}]")
            mix.append(f"[vo{j}]")
        chains.append(f"{''.join(mix)}amix=inputs={len(mix)}:duration=first:normalize=0,"
                      f"loudnorm=I=-14:TP=-1.5:LRA=11,aresample=48000[aout]")
        chains.append(f"{last}format=yuv420p[vout]")
        out = base_dir / spec["out"]
        draft = "--draft" in sys.argv
        subprocess.run(["ffmpeg", "-y", "-v", "error", *inputs, "-filter_complex", ";".join(chains),
                        "-map", "[vout]", "-map", "[aout]", "-r", fps, "-c:v", "libx264",
                        *(["-preset", "veryfast", "-crf", "24"] if draft else
                          ["-preset", "slow", "-crf", "17", "-maxrate", "18M", "-bufsize", "36M", "-profile:v", "high"]),
                        "-c:a", "aac", "-b:a", "256k", "-movflags", "+faststart", "-t", f"{total:.3f}", str(out)],
                       check=True)
        print(f"wrote {out} ({total:.1f} s, {W}x{H}, {len(vo_inputs)} narrator lines)")
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


if __name__ == "__main__":
    main()
