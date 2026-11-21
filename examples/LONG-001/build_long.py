#!/usr/bin/env python3
"""Assemble LONG-001: cold open, title, (number card, clip, reaction) x6, outro -> renders/LONG-001.mp4"""
import json, subprocess, sys
from pathlib import Path
from PIL import Image, ImageDraw, ImageFilter
sys.path.insert(0, "/home/claude/theft-talk-clipper/scripts")
import news_stills as ns

D = Path(__file__).resolve().parent
W, H = 1920, 1080
T = D / "tmp"; T.mkdir(exist_ok=True)
(D / "renders").mkdir(exist_ok=True)
L = json.loads((D / "vo/data/lines.json").read_text())["lines"]
VO = D / "vo/data/narration.wav"
ENC = ["-c:v", "libx264", "-preset", "veryfast", "-crf", "18", "-pix_fmt", "yuv420p", "-r", "30",
       "-c:a", "aac", "-b:a", "192k", "-ar", "48000", "-ac", "2"]

CLIPS = [  # (part, number, hindi title, streamer)
    ("p6_booth", 6, "टोल बूथ में फँस गया", "Jerma985"),
    ("p5_bella", 5, "प्लेन से व्हीली?", "TheBella26 · INDIA"),
    ("p4_plane", 4, "उल्टा प्लेन, सब ज़िंदा", "caseoh_"),
    ("p3_tower", 3, "वाइस सिटी का सबसे ऊँचा टावर", "Jerma985"),
    ("p2_atv", 2, "'इस बार क्रैश नहीं करेंगे'", "caseoh_"),
    ("p1_gator", 1, "बस एक और फ़ोटो", "Jerma985"),
]


def run(c):
    r = subprocess.run(c, capture_output=True, text=True)
    if r.returncode:
        sys.exit(r.stderr[-2000:])


def dur(f):
    return float(subprocess.check_output(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of",
                                          "csv=p=0", str(f)], text=True))


def frame(part, t, out):
    run(["ffmpeg", "-v", "error", "-y", "-ss", f"{t:.2f}", "-i", str(D / f"parts/{part}.mp4"), "-frames:v", "1", str(out)])
    return Image.open(out).convert("RGB")


def card_video(img, line_i, name, pad=0.45):
    png = T / f"{name}.png"; img.save(png)
    a, b = L[line_i]["start"] - 0.05, L[line_i]["end"] + pad
    out = T / f"{name}.mp4"
    run(["ffmpeg", "-v", "error", "-y", "-loop", "1", "-t", f"{b - a:.3f}", "-i", str(png),
         "-ss", f"{a:.3f}", "-t", f"{b - a:.3f}", "-i", str(VO),
         "-filter_complex", f"[0:v]scale={W}:{H},zoompan=z='min(zoom+0.0006,1.06)':d=1:s={W}x{H}:fps=30[v];"
                            f"[1:a]apad,atrim=0:{b - a:.3f},loudnorm=I=-14:TP=-1.5:LRA=11,aresample=48000[a]",
         "-map", "[v]", "-map", "[a]", "-t", f"{b - a:.3f}", *ENC, str(out)])
    return out


def neon(seed):
    return ns.background(W, H, seed).convert("RGBA")


def title_card():
    img = neon(41)
    ns.glow_text(img, (W // 2, 230), "GTA 6 LAUNCH", 150, ns.COL["cyan"], stroke=6)
    ns.glow_text(img, (W // 2, 420), "के 6 सबसे फनी पल", 130, ns.COL["pink"], stroke=6)
    ns.glow_text(img, (W // 2, 560), "@thefttalk", 60, ns.COL["gold"])
    return img.convert("RGB")


def outro_card():
    img = neon(43)
    ns.glow_text(img, (W // 2, 220), "कौन सा सबसे फनी था?", 120, ns.COL["pink"], stroke=6)
    ns.glow_text(img, (W // 2, 400), "#1 - #6  COMMENT KARO", 110, ns.COL["cyan"], stroke=6)
    ns.glow_text(img, (W // 2, 560), "SUBSCRIBE  @thefttalk", 80, ns.COL["gold"])
    return img.convert("RGB")


def number_card(part, n, title, streamer):
    base = frame(part, dur(D / f"parts/{part}.mp4") * 0.45, T / f"{part}_bg.jpg")
    bg = base.filter(ImageFilter.GaussianBlur(14))
    dark = Image.new("RGB", bg.size, (10, 0, 25))
    img = Image.blend(bg, dark, 0.55).convert("RGBA")
    ns.glow_text(img, (W // 2, 330), f"#{n}", 330, ns.COL["pink"], stroke=8)
    size = ns.fit_size(title, 120, W * 0.85)
    ns.glow_text(img, (W // 2, 620), title, size, ns.COL["cyan"], stroke=5)
    ns.glow_text(img, (W // 2, 790), streamer, 64, ns.COL["gold"])
    return img.convert("RGB")


def reaction_card(part, text):
    last = frame(part, dur(D / f"parts/{part}.mp4") - 0.1, T / f"{part}_last.jpg")
    img = Image.blend(last, Image.new("RGB", last.size, (0, 0, 0)), 0.35).convert("RGBA")
    size = ns.fit_size(text, 76, W * 0.86)
    ns.glow_text(img, (W // 2, H - 150), text, size, ns.COL["gold"], stroke=4)
    return img.convert("RGB")


def main():
    seq = []
    # cold open: 3.2 s around the gator lunge (slow-mo segment starts at 11.8 s in p1)
    co = T / "coldopen.mp4"
    run(["ffmpeg", "-v", "error", "-y", "-ss", "11.0", "-t", "3.4", "-i", str(D / "parts/p1_gator.mp4"),
         "-af", "afade=t=out:st=3.0:d=0.4", *ENC, str(co)])
    seq.append(co)
    seq.append(card_video(title_card(), 0, "title"))
    reactions = {"p6_booth": (2, "बेचारी अटेंडेंट भी सोच रही होगी, ये कौन आ गया"),
                 "p5_bella": (4, "दूसरी बार में प्लेन उड़ा ही दिया"),
                 "p4_plane": (6, "फ़िज़िक्स पर सवाल मत करो, बस मान लो"),
                 "p3_tower": (8, "ऊपर चढ़ने में मेहनत, नीचे आने में दो सेकंड"),
                 "p2_atv": (10, "प्रिस्टीन कंडीशन। बिल्कुल नई जैसी।"),
                 "p1_gator": (12, "फ़ोटो तो मिल गई। जर्मा नहीं बचा।")}
    for k, (part, n, title, streamer) in enumerate(CLIPS):
        seq.append(card_video(number_card(part, n, title, streamer), 1 + 2 * k, f"num{n}"))
        seq.append(D / f"parts/{part}.mp4")
        li, txt = reactions[part]
        seq.append(card_video(reaction_card(part, txt), li, f"react{n}", pad=0.3))
    seq.append(card_video(outro_card(), 13, "outro", pad=1.2))
    # concat (re-encode once so every piece shares one timeline)
    inputs, fc = [], ""
    for i, f in enumerate(seq):
        inputs += ["-i", str(f)]
        fc += f"[{i}:v]setsar=1,fps=30,format=yuv420p[v{i}];[{i}:a]aresample=48000,aformat=channel_layouts=stereo[a{i}];"
    fc += "".join(f"[v{i}][a{i}]" for i in range(len(seq))) + f"concat=n={len(seq)}:v=1:a=1[v][a]"
    out = D / "renders/LONG-001.mp4"
    run(["ffmpeg", "-v", "error", "-y", *inputs, "-filter_complex", fc, "-map", "[v]", "-map", "[a]",
         "-c:v", "libx264", "-preset", "veryfast", "-crf", "20", "-pix_fmt", "yuv420p", "-c:a", "aac", "-b:a", "192k",
         "-movflags", "+faststart", str(out)])
    # chapters for the description
    t, chap = 0.0, []
    names = ["Intro"] + [f"#{n} {s}" for _, n, _, s in CLIPS]
    marks = [1] + [2 + 3 * k for k in range(6)]
    for i, f in enumerate(seq):
        if i in marks:
            chap.append((t, names[marks.index(i)]))
        t += dur(f)
    (D / "renders/chapters.txt").write_text("\n".join(f"{int(a // 60)}:{int(a % 60):02d} {n}" for a, n in [(0, "Intro")] + chap[1:]) + "\n")
    print(out, f"{t:.1f} s")
    print((D / "renders/chapters.txt").read_text())


if __name__ == "__main__":
    main()
