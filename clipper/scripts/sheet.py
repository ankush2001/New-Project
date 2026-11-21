#!/usr/bin/env python3
"""sheet.py - contact sheets and QA frames for Theft Talk clips.

  python3 sheet.py scout <video> [--every 2] [--out sheet.jpg]
      grid of frames, one every N seconds, each stamped with its time. Use it on every
      candidate before trusting a title, and to find facecam / game crop boxes (pixel grid on frame 1).
  python3 sheet.py qa <render.mp4> [--out qa.jpg]
      full-size frames for QA: hook (0.5 s), flash (teaser end), payoff (78%), last frame.
  python3 sheet.py frame <video> <t> [--out f.jpg] [--grid]
      one full-size frame at t seconds; --grid draws a 100 px pixel grid for crop boxes.
"""
import json, subprocess, sys, tempfile
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont


def dur(v):
    return float(subprocess.check_output(["ffprobe", "-v", "error", "-show_entries", "format=duration",
                                          "-of", "csv=p=0", v], text=True).strip())


def grab(v, t, path, scale=None):
    vf = ["-vf", f"scale={scale}:-2"] if scale else []
    subprocess.run(["ffmpeg", "-y", "-v", "error", "-ss", f"{t:.2f}", "-i", v, "-frames:v", "1", *vf, path],
                   check=True)
    return Image.open(path).convert("RGB")


def font(n):
    for f in ["/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
              str(Path.home() / ".theft-talk/fonts/Anton-Regular.ttf")]:
        if Path(f).exists():
            return ImageFont.truetype(f, n)
    return ImageFont.load_default()


def label(im, txt, n=28):
    d = ImageDraw.Draw(im)
    d.rectangle([0, 0, len(txt) * n * 0.62 + 16, n + 12], fill="black")
    d.text((8, 4), txt, fill="yellow", font=font(n))
    return im


def tile(ims, cols):
    w, h = ims[0].size
    rows = (len(ims) + cols - 1) // cols
    sheet = Image.new("RGB", (w * cols, h * rows), "black")
    for i, im in enumerate(ims):
        sheet.paste(im.resize((w, h)), ((i % cols) * w, (i // cols) * h))
    return sheet


def opt(args, k, d):
    return args[args.index(k) + 1] if k in args else d


def main():
    a = sys.argv[1:]
    if len(a) < 2:
        sys.exit(__doc__)
    mode, v = a[0], a[1]
    tmp = tempfile.mkdtemp()
    if mode == "scout":
        every = float(opt(a, "--every", 2))
        D = dur(v)
        ts = [i * every for i in range(int(D // every) + 1) if i * every < D - 0.1]
        ims = [label(grab(v, t, f"{tmp}/{i}.jpg", 480), f"{t:.0f}s") for i, t in enumerate(ts)]
        out = opt(a, "--out", str(Path(v).with_suffix("")) + "_sheet.jpg")
        tile(ims, 6).save(out, quality=85)
    elif mode == "qa":
        D = dur(v)
        tl = Path(v + ".timeline.json")
        te = json.loads(tl.read_text())["teaser_end"] if tl.exists() else 3.0
        pts = [("hook 0.5s", 0.5), (f"flash {te + 0.05:.2f}s", te + 0.05), (f"after flash {te + 0.4:.2f}s", te + 0.4),
               (f"payoff {D * 0.78:.1f}s", D * 0.78), (f"last {D - 0.1:.1f}s", D - 0.1)]
        ims = [label(grab(v, t, f"{tmp}/q{i}.jpg"), n, 44) for i, (n, t) in enumerate(pts)]
        out = opt(a, "--out", str(Path(v).with_suffix("")) + "_qa.jpg")
        tile(ims, 5).save(out, quality=90)
    elif mode == "frame":
        t = float(a[2])
        im = grab(v, t, f"{tmp}/f.jpg")
        if "--grid" in a:
            d = ImageDraw.Draw(im)
            for x in range(0, im.width, 100):
                d.line([(x, 0), (x, im.height)], fill=(255, 0, 0), width=1)
                d.text((x + 2, 2), str(x), fill="yellow", font=font(16))
            for y in range(0, im.height, 100):
                d.line([(0, y), (im.width, y)], fill=(255, 0, 0), width=1)
                d.text((2, y + 2), str(y), fill="yellow", font=font(16))
        out = opt(a, "--out", str(Path(v).with_suffix("")) + f"_{t:.1f}.jpg")
        im.save(out, quality=92)
    else:
        sys.exit(__doc__)
    print(out)


if __name__ == "__main__":
    main()
