#!/usr/bin/env python3
"""news_stills.py - neon synthwave news stills for Theft Talk (no game art, all drawn in code).

  python3 news_stills.py <project>      reads <project>/stills.json, writes <project>/footage/<id>.mp4 (+ .png)
                                        and <project>/review/stills.jpg (contact sheet - LOOK at it)

stills.json: {"size":[1080,1920], "seconds":6, "stills":[ {...}, ... ]}
Each still: {"id":"s1", "kind":..., "seed":3, ...fields}
  big       "top": small label above, "big": huge number/word, "sub": line under, "color": "pink|cyan|gold|green|red"
  bar       "label", "items":[{"name":"GTA 5","value":815,"show":"$815M"},{"name":"GTA 6","value":2360,"show":"$2.36B"}]
  calendar  "month":"NOV", "day":"19", "sub":"2026"
  download  "big":"212 GB", "pct":0.72, "sub":"PS5 / XBOX"
  lock      "big":"NOT YET", "sub":"OFFICIAL NUMBERS"
  card      "lines":["TAKE-TWO", "HAS NOT RELEASED", "OFFICIAL SALES"], "sub":"ESTIMATES ONLY"
  times     "big":"3X", "sub":"GTA 5 DAY ONE"
Text may be Devanagari (shaped with raqm). Graphics live in the top 66% so captions fit over the sea.
"""
import json, math, random, subprocess, sys
from pathlib import Path
from PIL import Image, ImageDraw, ImageFilter, ImageFont, features

H = Path.home()
ANTON = str(H / ".theft-talk/fonts/Anton-Regular.ttf")
DEVA = str(H / ".faceless-shorts/fonts/NotoSansDevanagari.ttf")
COL = {"pink": (255, 60, 170), "cyan": (60, 230, 255), "gold": (255, 200, 60), "green": (80, 255, 140),
       "red": (255, 70, 70), "white": (255, 255, 255)}
RAQM = features.check("raqm")


def font(txt, size):
    if any("ऀ" <= c <= "ॿ" for c in txt) or any(c in txt for c in "₹≈"):
        f = ImageFont.truetype(DEVA, size, layout_engine=ImageFont.Layout.RAQM if RAQM else ImageFont.Layout.BASIC)
        try:
            f.set_variation_by_axes([800, 100])
        except Exception:
            pass
        return f
    return ImageFont.truetype(ANTON, size)


def background(W, Hh, seed):
    rnd = random.Random(seed)
    img = Image.new("RGB", (W, Hh))
    d = ImageDraw.Draw(img)
    horizon = int(Hh * 0.70)
    top, mid, low = (18, 6, 48), (120, 20, 120), (255, 110, 60)
    for y in range(horizon):
        t = y / horizon
        c = [int(top[i] + (mid[i] - top[i]) * min(1, t * 1.6)) if t < 0.62 else
             int(mid[i] + (low[i] - mid[i]) * ((t - 0.62) / 0.38)) for i in range(3)]
        d.line([(0, y), (W, y)], fill=tuple(c))
    for _ in range(140):  # stars
        x, y = rnd.randrange(W), rnd.randrange(int(horizon * 0.5))
        d.point((x, y), fill=(255, 255, 255))
    # sun with stripes
    sun = Image.new("RGBA", (W, Hh), (0, 0, 0, 0))
    sd = ImageDraw.Draw(sun)
    r = int(W * 0.30)
    cx, cy = W // 2, horizon - int(r * 0.35)
    for y in range(cy - r, cy + r):
        t = (y - (cy - r)) / (2 * r)
        col = (255, int(220 - 140 * t), int(80 + 60 * t), 255)
        half = int(math.sqrt(max(0, r * r - (y - cy) ** 2)))
        if t > 0.45 and int((y - cy) / max(4, 18 - 10 * t)) % 2:
            continue
        sd.line([(cx - half, y), (cx + half, y)], fill=col)
    img.paste(sun, (0, 0), sun)
    # palms + skyline silhouettes
    x = 0
    while x < W:
        bw = rnd.randint(40, 110)
        bh = rnd.randint(int(Hh * 0.04), int(Hh * (0.20 if abs(x - W / 2) > W * 0.25 else 0.10)))
        d.rectangle([x, horizon - bh, x + bw, horizon], fill=(28, 8, 40))
        for wy in range(horizon - bh + 12, horizon - 8, 22):
            for wx in range(x + 8, x + bw - 8, 16):
                if rnd.random() < 0.35:
                    d.rectangle([wx, wy, wx + 6, wy + 9], fill=(255, 190, 90) if rnd.random() < .7 else (80, 230, 255))
        x += bw + rnd.randint(2, 18)
    for px in (rnd.randint(30, 160), W - rnd.randint(60, 200)):
        bx, by = px, horizon
        top_y = horizon - rnd.randint(int(Hh * .18), int(Hh * .26))
        d.line([(bx, by), (bx + 18, top_y)], fill=(10, 0, 20), width=14)
        for a in range(0, 360, 40):
            ex = bx + 18 + int(math.cos(math.radians(a)) * 120)
            ey = top_y + int(math.sin(math.radians(a)) * 50) + 30
            d.line([(bx + 18, top_y), (ex, ey)], fill=(10, 0, 20), width=10)
    # sea with reflections
    for y in range(horizon, Hh):
        t = (y - horizon) / (Hh - horizon)
        d.line([(0, y), (W, y)], fill=(int(40 - 30 * t), int(10 + 10 * t), int(70 - 30 * t)))
    for _ in range(90):
        y = rnd.randint(horizon + 4, Hh - 4)
        w = rnd.randint(20, 160)
        x0 = W // 2 - int(r * (1 - (y - horizon) / (Hh - horizon) * 0.3)) + rnd.randint(0, 2 * r)
        d.line([(x0, y), (x0 + w, y)], fill=(255, 120, 120) if rnd.random() < .6 else (255, 60, 170), width=2)
    return img


def glow_text(img, xy, txt, size, color, anchor="mm", stroke=6):
    f = font(txt, size)
    layer = Image.new("RGBA", img.size, (0, 0, 0, 0))
    ImageDraw.Draw(layer).text(xy, txt, font=f, fill=color + (255,), anchor=anchor, stroke_width=stroke,
                               stroke_fill=color + (255,))
    img.paste(layer.filter(ImageFilter.GaussianBlur(18)), (0, 0), layer.filter(ImageFilter.GaussianBlur(18)))
    ImageDraw.Draw(img).text(xy, txt, font=f, fill=(255, 255, 255), anchor=anchor, stroke_width=3,
                             stroke_fill=(20, 0, 30))
    return f


def fit_size(txt, start, maxw):
    s = start
    while s > 30:
        f = font(txt, s)
        if f.getbbox(txt)[2] - f.getbbox(txt)[0] <= maxw:
            return s
        s -= 6
    return s


def panel(img, box, color):
    layer = Image.new("RGBA", img.size, (0, 0, 0, 0))
    dl = ImageDraw.Draw(layer)
    dl.rounded_rectangle(box, 36, fill=(15, 0, 35, 190), outline=color + (255,), width=6)
    g = layer.filter(ImageFilter.GaussianBlur(10))
    img.paste(g, (0, 0), g)
    img.paste(layer, (0, 0), layer)


def draw(st, W, Hh):
    img = background(W, Hh, st.get("seed", 1)).convert("RGBA")
    c = COL.get(st.get("color", "pink"), COL["pink"])
    k = st["kind"]
    top_y, mid_y = int(Hh * .16), int(Hh * .36)
    if st.get("top"):
        glow_text(img, (W // 2, top_y), st["top"], fit_size(st["top"], 90, W * .86), COL["cyan"])
    if k in ("big", "times"):
        glow_text(img, (W // 2, mid_y), st["big"], fit_size(st["big"], 300, W * .9), c, stroke=8)
        if st.get("sub"):
            glow_text(img, (W // 2, int(Hh * .52)), st["sub"], fit_size(st["sub"], 84, W * .86), COL["gold"])
    elif k == "bar":
        items = st["items"]
        mx = max(i["value"] for i in items)
        panel(img, (60, int(Hh * .22), W - 60, int(Hh * .60)), c)
        if st.get("label"):
            glow_text(img, (W // 2, int(Hh * .26)), st["label"], fit_size(st["label"], 70, W * .8), COL["cyan"])
        n = len(items)
        for j, it in enumerate(items):
            y = int(Hh * (.33 + j * (.22 / max(1, n - 1 if n > 1 else 1))))
            ImageDraw.Draw(img).text((110, y), it["name"], font=font(it["name"], 64), fill=(255, 255, 255),
                                     anchor="lm")
            bw = int((W - 420) * it["value"] / mx)
            col = COL["gold"] if j == n - 1 else COL["cyan"]
            ImageDraw.Draw(img).rounded_rectangle((110, y + 50, 110 + bw, y + 130), 20, fill=col)
            ImageDraw.Draw(img).text((130 + bw, y + 90), it["show"], font=font(it["show"], 72), fill=(255, 255, 255),
                                     anchor="lm", stroke_width=3, stroke_fill=(20, 0, 30))
    elif k == "calendar":
        x0, y0, x1, y1 = W * .2, Hh * .2, W * .8, Hh * .55
        panel(img, (x0, y0, x1, y1), c)
        ImageDraw.Draw(img).rounded_rectangle((x0, y0, x1, y0 + 170), 36, fill=c)
        ImageDraw.Draw(img).text((W // 2, y0 + 85), st["month"], font=font(st["month"], 120), fill=(255, 255, 255),
                                 anchor="mm")
        glow_text(img, (W // 2, int((y0 + 170 + y1) / 2)), st["day"], 330, COL["white"], stroke=4)
        if st.get("sub"):
            glow_text(img, (W // 2, int(Hh * .61)), st["sub"], fit_size(st["sub"], 84, W * .8), COL["gold"])
    elif k == "download":
        glow_text(img, (W // 2, mid_y), st["big"], fit_size(st["big"], 260, W * .9), c, stroke=8)
        y = int(Hh * .48)
        d = ImageDraw.Draw(img)
        d.rounded_rectangle((100, y, W - 100, y + 70), 35, outline=(255, 255, 255), width=5)
        d.rounded_rectangle((112, y + 12, 112 + int((W - 224) * st.get("pct", .7)), y + 58), 25, fill=COL["green"])
        if st.get("sub"):
            glow_text(img, (W // 2, int(Hh * .57)), st["sub"], fit_size(st["sub"], 80, W * .86), COL["gold"])
    elif k == "lock":
        d = ImageDraw.Draw(img)
        cx, cy = W // 2, int(Hh * .30)
        d.arc((cx - 120, cy - 230, cx + 120, cy + 10), 180, 360, fill=c, width=40)
        d.rounded_rectangle((cx - 190, cy - 60, cx + 190, cy + 200), 30, fill=c)
        d.ellipse((cx - 30, cy + 40, cx + 30, cy + 100), fill=(20, 0, 30))
        glow_text(img, (W // 2, int(Hh * .48)), st["big"], fit_size(st["big"], 170, W * .9), COL["red"])
        if st.get("sub"):
            glow_text(img, (W // 2, int(Hh * .56)), st["sub"], fit_size(st["sub"], 80, W * .86), COL["gold"])
    elif k == "card":
        panel(img, (70, int(Hh * .20), W - 70, int(Hh * .58)), c)
        ls = st["lines"]
        for j, ln in enumerate(ls):
            y = int(Hh * (.28 + j * (.22 / max(1, len(ls) - 1))))
            glow_text(img, (W // 2, y), ln, fit_size(ln, 130, W * .8), COL["cyan"] if j == 0 else COL["white"],
                      stroke=4)
        if st.get("sub"):
            glow_text(img, (W // 2, int(Hh * .63)), st["sub"], fit_size(st["sub"], 70, W * .86), COL["gold"])
    else:
        raise SystemExit(f"unknown kind {k}")
    return img.convert("RGB")


def draw_land(st, W, Hh):
    """16:9 layout: graphics in the top 70%, captions go over the sea at ~88%."""
    img = background(W, Hh, st.get("seed", 1)).convert("RGBA")
    c = COL.get(st.get("color", "pink"), COL["pink"])
    k = st["kind"]
    Y = lambda f: int(Hh * f)
    if st.get("top") and k in ("big", "times", "download"):
        glow_text(img, (W // 2, Y(.12)), st["top"], fit_size(st["top"], 80, W * .7), COL["cyan"])
    if k in ("big", "times"):
        glow_text(img, (W // 2, Y(.37)), st["big"], fit_size(st["big"], 270, W * .8), c, stroke=8)
        if st.get("sub"):
            glow_text(img, (W // 2, Y(.61)), st["sub"], fit_size(st["sub"], 72, W * .7), COL["gold"])
    elif k == "bar":
        x0, x1 = int(W * .18), int(W * .82)
        panel(img, (x0, Y(.08), x1, Y(.66)), c)
        if st.get("label"):
            glow_text(img, (W // 2, Y(.15)), st["label"], fit_size(st["label"], 64, (x1 - x0) * .9), COL["cyan"])
        items = st["items"]; mx = max(i["value"] for i in items); n = len(items)
        d = ImageDraw.Draw(img)
        for j, it in enumerate(items):
            y = Y(.25 + j * (.20 / max(1, n - 1)))
            d.text((x0 + 50, y), it["name"], font=font(it["name"], 56), fill=(255, 255, 255), anchor="lm")
            bw = int((x1 - x0 - 380) * it["value"] / mx)
            col = COL["gold"] if j == n - 1 else COL["cyan"]
            d.rounded_rectangle((x0 + 50, y + 42, x0 + 50 + bw, y + 112), 18, fill=col)
            d.text((x0 + 70 + bw, y + 77), it["show"], font=font(it["show"], 64), fill=(255, 255, 255), anchor="lm",
                   stroke_width=3, stroke_fill=(20, 0, 30))
    elif k == "calendar":
        x0, y0, x1, y1 = W * .38, Hh * .07, W * .62, Hh * .58
        panel(img, (x0, y0, x1, y1), c)
        ImageDraw.Draw(img).rounded_rectangle((x0, y0, x1, y0 + 130), 36, fill=c)
        ImageDraw.Draw(img).text((W // 2, y0 + 65), st["month"], font=font(st["month"], 96), fill=(255, 255, 255), anchor="mm")
        glow_text(img, (W // 2, int((y0 + 130 + y1) / 2)), st["day"], 240, COL["white"], stroke=4)
        if st.get("sub"):
            glow_text(img, (W // 2, Y(.66)), st["sub"], fit_size(st["sub"], 70, W * .7), COL["gold"])
    elif k == "download":
        glow_text(img, (W // 2, Y(.33)), st["big"], fit_size(st["big"], 240, W * .8), c, stroke=8)
        d = ImageDraw.Draw(img); y = Y(.50); xa, xb = int(W * .22), int(W * .78)
        d.rounded_rectangle((xa, y, xb, y + 60), 30, outline=(255, 255, 255), width=5)
        d.rounded_rectangle((xa + 12, y + 12, xa + 12 + int((xb - xa - 24) * st.get("pct", .7)), y + 48), 20, fill=COL["green"])
        if st.get("sub"):
            glow_text(img, (W // 2, Y(.63)), st["sub"], fit_size(st["sub"], 70, W * .7), COL["gold"])
    elif k == "lock":
        d = ImageDraw.Draw(img); cx, cy = W // 2, Y(.24)
        d.arc((cx - 95, cy - 180, cx + 95, cy + 10), 180, 360, fill=c, width=32)
        d.rounded_rectangle((cx - 150, cy - 50, cx + 150, cy + 150), 26, fill=c)
        d.ellipse((cx - 24, cy + 30, cx + 24, cy + 78), fill=(20, 0, 30))
        glow_text(img, (W // 2, Y(.53)), st["big"], fit_size(st["big"], 150, W * .7), COL["red"])
        if st.get("sub"):
            glow_text(img, (W // 2, Y(.64)), st["sub"], fit_size(st["sub"], 64, W * .7), COL["gold"])
    elif k == "card":
        panel(img, (int(W * .22), Y(.07), int(W * .78), Y(.60)), c)
        ls = st["lines"]
        for j, ln in enumerate(ls):
            y = Y(.18 + j * (.30 / max(1, len(ls) - 1)))
            glow_text(img, (W // 2, y), ln, fit_size(ln, 110, W * .5), COL["cyan"] if j == 0 else COL["white"], stroke=4)
        if st.get("sub"):
            glow_text(img, (W // 2, Y(.67)), st["sub"], fit_size(st["sub"], 64, W * .7), COL["gold"])
    else:
        raise SystemExit(f"unknown kind {k}")
    return img.convert("RGB")


def main():
    P = Path(sys.argv[1]).resolve()
    S = json.loads((P / "stills.json").read_text(encoding="utf-8"))
    W, Hh = S.get("size", [1080, 1920])
    secs = S.get("seconds", 6)
    (P / "footage").mkdir(exist_ok=True)
    (P / "review").mkdir(exist_ok=True)
    thumbs = []
    for st in S["stills"]:
        im = draw_land(st, W, Hh) if W > Hh else draw(st, W, Hh)
        png = P / "footage" / f"{st['id']}.png"
        im.save(png)
        subprocess.run(["ffmpeg", "-y", "-v", "error", "-loop", "1", "-t", str(secs), "-i", str(png), "-r", "30",
                        "-c:v", "libx264", "-preset", "veryfast", "-crf", "16", "-pix_fmt", "yuv420p",
                        str(P / "footage" / f"{st['id']}.mp4")], check=True)
        thumbs.append(im.resize((W // 4, Hh // 4)))
    cols = min(5, len(thumbs))
    rows = (len(thumbs) + cols - 1) // cols
    sheet = Image.new("RGB", (cols * W // 4, rows * Hh // 4))
    for i, t in enumerate(thumbs):
        sheet.paste(t, ((i % cols) * W // 4, (i // cols) * Hh // 4))
    sheet.save(P / "review" / "stills.jpg", quality=88)
    print(P / "review" / "stills.jpg")


if __name__ == "__main__":
    main()
