#!/usr/bin/env python3
"""LONG-002 assembler: 16:9 stills cut on narration lines, slow push-in, Devanagari captions, deep voice."""
import json, subprocess, sys
from pathlib import Path
from PIL import Image, ImageDraw
sys.path.insert(0, "/home/claude/theft-talk-clipper/scripts")
import news_stills as ns

D = Path(__file__).resolve().parent
W, H, FPS = 1920, 1080, 30
S = json.loads((D / "script.json").read_text())
L = json.loads((D / "data/lines.json").read_text())
T = D / "tmp"; T.mkdir(exist_ok=True); (D / "renders").mkdir(exist_ok=True)
total = L["duration"]


def run(c):
    r = subprocess.run(c, capture_output=True, text=True)
    if r.returncode:
        sys.exit(r.stderr[-2000:])


def caption_png(text, path):
    img = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    f = ns.font(text, 58)
    words, lines, cur = text.split(), [], ""
    for w in words:
        t = (cur + " " + w).strip()
        if d.textlength(t, font=f) <= W * 0.78 or not cur:
            cur = t
        else:
            lines.append(cur); cur = w
    lines.append(cur)
    lh = 78
    y0 = int(H * 0.86) - (len(lines) - 1) * lh // 2
    wmax = max(d.textlength(l, font=f) for l in lines)
    d.rounded_rectangle((W / 2 - wmax / 2 - 30, y0 - 50, W / 2 + wmax / 2 + 30, y0 + (len(lines) - 1) * lh + 50), 22,
                        fill=(10, 0, 25, 170))
    for i, l in enumerate(lines):
        d.text((W // 2, y0 + i * lh), l, font=f, fill=(255, 255, 255), anchor="mm", stroke_width=3,
               stroke_fill=(20, 0, 30))
    img.save(path)


# segments: each line shows its still from its start (first line from 0) to the next line's start
segs = []
for i, ln in enumerate(S["lines"]):
    a = 0.0 if i == 0 else L["lines"][i]["start"]
    b = L["lines"][i + 1]["start"] if i + 1 < len(S["lines"]) else total
    segs.append((ln["still"], a, b, ln["text"].replace("पीएस फ़ाइव", "PS5").replace("एक्सबॉक्स", "Xbox")
                 .replace("पीएस फ़ोर", "PS4")))
parts = []
for i, (still, a, b, text) in enumerate(segs):
    n = max(1, round((b - a) * FPS))
    cap = T / f"cap{i:02d}.png"; caption_png(text, cap)
    out = T / f"seg{i:02d}.mp4"
    z = 0.10 * (n / FPS) / 12  # gentle push, ~0.1 per 12 s
    run(["ffmpeg", "-v", "error", "-y", "-loop", "1", "-i", str(D / f"footage/{still}.png"), "-i", str(cap),
         "-filter_complex",
         f"[0:v]scale={W * 2}:{H * 2},zoompan=z='1+{z:.4f}*on/{n}':x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':d={n}:s={W}x{H}:fps={FPS}[bg];"
         f"[bg][1:v]overlay=0:0,format=yuv420p[v]",
         "-map", "[v]", "-frames:v", str(n), "-c:v", "libx264", "-preset", "veryfast", "-crf", "18", str(out)])
    parts.append(out)
lst = T / "list.txt"; lst.write_text("".join(f"file '{p}'\n" for p in parts))
out = D / "renders/LONG-002.mp4"
run(["ffmpeg", "-v", "error", "-y", "-f", "concat", "-safe", "0", "-i", str(lst), "-i", str(D / "data/narration.wav"),
     "-filter_complex", "[1:a]loudnorm=I=-14:TP=-1.5:LRA=11,aresample=48000[a]", "-map", "0:v", "-map", "[a]",
     "-c:v", "libx264", "-preset", "medium", "-crf", "21", "-pix_fmt", "yuv420p", "-c:a", "aac", "-b:a", "192k",
     "-shortest", "-movflags", "+faststart", str(out)])
print(out)
# chapters
chap = [(0, "Intro"), (L["lines"][2]["start"], "Day one sales"), (L["lines"][8]["start"], "Streaming records"),
        (L["lines"][12]["start"], "India price"), (L["lines"][18]["start"], "GTA 5 legacy"),
        (L["lines"][20]["start"], "Official numbers?")]
(D / "renders/chapters.txt").write_text("\n".join(f"{int(t // 60)}:{int(t % 60):02d} {n}" for t, n in chap) + "\n")
print((D / "renders/chapters.txt").read_text())
