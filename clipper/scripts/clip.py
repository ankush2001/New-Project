#!/usr/bin/env python3
"""clip.py - Theft Talk streamer-clip renderer (one JSON spec -> one finished video).

Usage:
    python3 clip.py spec.json [--draft] [--no-loudnorm]

Every time in the spec is a SOURCE-clip second. clip.py builds the output timeline
(teaser -> flash + whoosh -> keep ranges with one slow-mo/freeze) and maps all text onto it.

Spec fields (paths are relative to the spec file):
  src            source video (the downloaded clip)
  out            output mp4, e.g. "renders/TT-001.mp4"
  credit         "@streamer (Twitch)"  - always on screen, small
  handle         "@thefttalk"          - optional, shown after the credit
  size           [1080,1920] Short (default) or [1920,1080] long-form / compile part
  layout         "stack"  facecam crop on top, gameplay crop below (vertical, default)
                 "fit"    gameplay only, whole width, blurred fill above/below (no facecam)
                 "full"   gameplay crop fills the frame
                 "pip"    16:9: gameplay full frame, facecam inset top-right
  facecam        [x,y,w,h] crop of the cam in source pixels (stack / pip)
  game           [x,y,w,h] crop of the gameplay in source pixels (no chat, no cam, no watermark)
  split          stack only: share of height for the facecam panel (default 0.40)
  teaser         {"start":s,"end":e}  payoff shown first (2-4 s, from a DIFFERENT part than the full play)
  teaser_text    hook text during the teaser (ALL CAPS, adds context, never describes)
  keep           [[a,b], ...] source ranges for the full play, in order
  slowmo         {"start":a,"end":b,"speed":0.4}   one only, inside keep
  freeze         {"at":t,"dur":0.8}                one only, inside keep (use slowmo OR freeze)
  punchlines     [{"start":a,"end":b,"text":"INSURANCE: DENIED"}]  source times, inside keep
  subtitles      "subs.srt" in SOURCE seconds; cues outside the teaser/keep ranges are dropped
  lang_font      "deva" for Devanagari text (Hindi), default latin
  volume         gain before loudness normalisation (default 1.0)
  flash          true (default) white flash + whoosh at the teaser cut
  end_freeze     seconds to hold the last frame (e.g. WASTED before a black loading screen), default 0
  banner         {"text":"SPEED FOUND THE RED HULK MISSION","badge":"GTA 6","color":"pink"}  stack only:
                 a title bar across the top for the whole video (our own neon badge, never Rockstar art)
  punch          {"start":a,"end":b,"zoom":1.25}  hard punch-in on the gameplay for a source range (the
                 default comedic edit since 23 Nov; slow-mo only if a spec asks for it)

Outputs: <out>, plus <out>.timeline.json (segment map) for QA.
"""
import json, math, os, shutil, subprocess, sys, tempfile, urllib.request
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

FONT_DIR = Path.home() / ".theft-talk" / "fonts"
FONT_URLS = {
    "Anton-Regular.ttf": "https://raw.githubusercontent.com/google/fonts/main/ofl/anton/Anton-Regular.ttf",
    "NotoSansDevanagari.ttf": "https://raw.githubusercontent.com/google/fonts/main/ofl/notosansdevanagari/NotoSansDevanagari%5Bwdth%2Cwght%5D.ttf",
}
FALLBACKS = ["/usr/share/fonts/truetype/google-fonts/Poppins-Bold.ttf",
             "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
             "/System/Library/Fonts/Supplemental/Impact.ttf",
             "/Library/Fonts/Arial Bold.ttf"]
FPS = 30


def die(msg):
    sys.exit(f"clip.py: {msg}")


def run(cmd):
    r = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    if r.returncode:
        die("ffmpeg failed:\n" + " ".join(cmd) + "\n" + r.stderr[-3000:])
    return r


def font_path(kind):
    name = "NotoSansDevanagari.ttf" if kind == "deva" else "Anton-Regular.ttf"
    p = FONT_DIR / name
    if not p.exists():
        try:
            FONT_DIR.mkdir(parents=True, exist_ok=True)
            urllib.request.urlretrieve(FONT_URLS[name], p)
        except Exception:
            pass
    if p.exists() and p.stat().st_size > 10000:
        return str(p)
    for f in FALLBACKS:
        if os.path.exists(f):
            return f
    return None


def probe(src):
    r = run(["ffprobe", "-v", "error", "-show_entries", "stream=codec_type,width,height:format=duration",
             "-of", "json", src])
    j = json.loads(r.stdout)
    v = next(s for s in j["streams"] if s["codec_type"] == "video")
    has_a = any(s["codec_type"] == "audio" for s in j["streams"])
    return v["width"], v["height"], float(j["format"]["duration"]), has_a


# ---------- timeline ----------
def build_segments(spec, dur):
    segs = []  # dicts: kind play|freeze, a, b, speed, part teaser|main
    t = spec.get("teaser")
    if t:
        segs.append(dict(kind="play", a=t["start"], b=t["end"], speed=1.0, part="teaser"))
    keep = spec.get("keep") or [[0, dur]]
    sm, fr, pu = spec.get("slowmo"), spec.get("freeze"), spec.get("punch")
    if sm and fr:
        print("warning: both slowmo and freeze set - the guide allows one comedic edit; using both anyway")
    for a, b in keep:
        cuts = sorted({a, b} | {x for x in ([sm["start"], sm["end"]] if sm else []) + ([fr["at"]] if fr else [])
                                + ([pu["start"], pu["end"]] if pu else []) if a < x < b})
        for i in range(len(cuts) - 1):
            x, y = cuts[i], cuts[i + 1]
            speed = sm["speed"] if sm and sm["start"] <= x and y <= sm["end"] else 1.0
            if fr and abs(x - fr["at"]) < 1e-6:
                segs.append(dict(kind="freeze", a=x, b=x, dur=fr["dur"], speed=1.0, part="main"))
            zoom = pu.get("zoom", 1.25) if pu and pu["start"] <= x and y <= pu["end"] else 1.0
            segs.append(dict(kind="play", a=x, b=y, speed=speed, part="main", zoom=zoom))
        if fr and abs(b - fr["at"]) < 1e-6:
            segs.append(dict(kind="freeze", a=b, b=b, dur=fr["dur"], speed=1.0, part="main"))
    if spec.get("end_freeze"):
        last = segs[-1]["b"]
        segs.append(dict(kind="freeze", a=last - 1 / FPS, b=last - 1 / FPS, dur=spec["end_freeze"], speed=1.0,
                         part="main"))
    o = 0.0
    for s in segs:
        s["len"] = s["dur"] if s["kind"] == "freeze" else (s["b"] - s["a"]) / s["speed"]
        s["o0"], o = o, o + s["len"]
        s["o1"] = o
    return segs, o


def map_t(segs, t, part="main", end=False):
    """source time -> output time within the given part; None if not kept."""
    cands = [s for s in segs if s["part"] == part and s["kind"] == "play" and s["a"] - 1e-6 <= t <= s["b"] + 1e-6]
    if not cands:
        return None
    s = cands[-1] if end else cands[0]
    out = s["o0"] + (t - s["a"]) / s["speed"]
    if end:  # include a freeze that sits exactly at this time
        for f in segs:
            if f["kind"] == "freeze" and f["part"] == part and abs(f["a"] - t) < 1e-6 and f["o0"] >= out - 1e-6:
                out = f["o1"]
    return out


def map_range(segs, a, b, parts=("teaser", "main")):
    """map a source range onto output (teaser and/or main); returns list of (o0,o1)."""
    res = []
    for part in parts:
        ps = [s for s in segs if s["part"] == part and s["kind"] == "play"]
        if not ps:
            continue
        lo, hi = max(a, min(s["a"] for s in ps)), min(b, max(s["b"] for s in ps))
        if hi - lo < 0.05:
            continue
        o0, o1 = map_t(segs, lo, part), map_t(segs, hi, part, end=True)
        if o0 is not None and o1 is not None and o1 > o0:
            res.append((o0, o1))
    return res


def parse_srt(path):
    cues, block = [], []
    def ts(x):
        h, m, s = x.strip().replace(",", ".").split(":")
        return int(h) * 3600 + int(m) * 60 + float(s)
    for line in list(open(path, encoding="utf-8-sig").read().splitlines()) + [""]:
        if line.strip():
            block.append(line)
            continue
        if len(block) >= 2:
            i = 1 if "-->" in block[1] else 0
            a, b = block[i].split("-->")
            cues.append((ts(a), ts(b), " ".join(block[i + 1:]).strip()))
        block = []
    return cues


# ---------- video per segment ----------
def layout_filter(spec, W, H, inp="[0:v]"):
    L = spec.get("layout", "stack")
    g = spec.get("game")
    gc = f"crop={g[2]}:{g[3]}:{g[0]}:{g[1]}," if g else ""
    fill = lambda w, h: f"scale={w}:{h}:force_original_aspect_ratio=increase,crop={w}:{h},setsar=1"
    if L == "stack":
        f = spec.get("facecam") or die("stack layout needs facecam [x,y,w,h]")
        bb = banner_h(spec, H)
        Hs = H - bb
        th = int(round(Hs * spec.get("split", 0.40) / 2) * 2)
        bh = Hs - th
        pad = f",pad={W}:{H}:0:{bb}:color=0x12061f" if bb else ""
        return (f"{inp}split[a][b];[a]crop={f[2]}:{f[3]}:{f[0]}:{f[1]},{fill(W, th)}[t];"
                f"[b]{gc}{fill(W, bh)}[g];[t][g]vstack,drawbox=y={th - 3}:w={W}:h=6:color=white@0.9:t=fill"
                f"{pad}"), bb + th
    if L == "fit":
        return (f"{inp}{gc}split[a][b];[a]{fill(W, H)},boxblur=24:2,eq=brightness=-0.18[bg];"
                f"[b]scale={W}:-2,setsar=1[fg];[bg][fg]overlay=(W-w)/2:(H-h)/2"), 0
    if L == "full":
        return f"{inp}{gc}{fill(W, H)}", 0
    if L == "pip":
        f = spec.get("facecam") or die("pip layout needs facecam [x,y,w,h]")
        pw = int(W * 0.26) // 2 * 2
        ph = int(pw * f[3] / f[2]) // 2 * 2
        return (f"{inp}split[a][b];[a]{gc}{fill(W, H)}[g];[b]crop={f[2]}:{f[3]}:{f[0]}:{f[1]},scale={pw}:{ph},"
                f"pad={pw + 8}:{ph + 8}:4:4:white[c];[g][c]overlay=W-w-40:40"), 0
    die(f"unknown layout {L}")


def banner_h(spec, H):
    return int(round(H * 0.135 / 2) * 2) if spec.get("banner") and spec.get("layout", "stack") == "stack" else 0


def zoomed(spec, z):
    """copy of spec whose game crop is tightened around its centre by factor z (punch-in)."""
    g = spec.get("game")
    if not g or z == 1.0:
        return spec
    w, h = int(g[2] / z) // 2 * 2, int(g[3] / z) // 2 * 2
    sp = dict(spec)
    sp["game"] = [g[0] + (g[2] - w) // 2, g[1] + (g[3] - h) // 2, w, h]
    return sp


BCOL = {"pink": (255, 60, 170), "cyan": (60, 230, 255), "gold": (255, 200, 60), "green": (80, 255, 140),
        "red": (255, 70, 70)}


def banner_png(path, W, H, spec, fontfile):
    from PIL import ImageFilter
    bn = spec["banner"]
    bb = banner_h(spec, H)
    k = W / 1080
    col = BCOL.get(bn.get("color", "pink"), BCOL["pink"])
    img = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    # dark band with a neon line under it
    for y in range(bb):
        t = y / max(1, bb - 1)
        d.line([(0, y), (W, y)], fill=(int(18 + 22 * t), int(6 + 4 * t), int(31 + 30 * t), 255))
    d.rectangle([0, bb - int(6 * k), W, bb], fill=col + (255,))
    # badge
    badge = bn.get("badge", "GTA 6")
    bf = ImageFont.truetype(fontfile, int(78 * k)) if fontfile else ImageFont.load_default()
    bw = d.textlength(badge, font=bf)
    bx0, by0 = int(30 * k), int((bb - 120 * k) / 2)
    bx1, by1 = bx0 + int(bw + 44 * k), by0 + int(120 * k)
    glow = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    gd = ImageDraw.Draw(glow)
    gd.rounded_rectangle([bx0, by0, bx1, by1], radius=int(22 * k), outline=col + (255,), width=int(10 * k))
    glow = glow.filter(ImageFilter.GaussianBlur(int(10 * k)))
    img.alpha_composite(glow)
    d = ImageDraw.Draw(img)
    d.rounded_rectangle([bx0, by0, bx1, by1], radius=int(22 * k), fill=(10, 4, 20, 255), outline=col + (255,),
                        width=int(6 * k))
    d.text(((bx0 + bx1) / 2, (by0 + by1) / 2), badge, font=bf, fill="white", anchor="mm",
           stroke_width=int(2 * k), stroke_fill=col)
    # title, up to two lines, shrink to fit
    text = bn["text"].upper()
    x0 = bx1 + int(26 * k)
    maxw = W - x0 - int(26 * k)
    for size in range(int(64 * k), int(34 * k), -2):
        tf = ImageFont.truetype(fontfile, size) if fontfile else ImageFont.load_default()
        lines = wrap(d, text, tf, maxw)
        if len(lines) <= 2:
            break
    lh = int(size * 1.08)
    ty = (bb - lh * len(lines)) / 2
    for i, ln in enumerate(lines[:2]):
        d.text((x0, ty + i * lh), ln, font=tf, fill="white", stroke_width=max(2, size // 14), stroke_fill="black")
    img.save(path)


def atempo(speed):
    parts, s = [], speed
    while s < 0.5:
        parts.append("atempo=0.5")
        s /= 0.5
    parts.append(f"atempo={s:.4f}")
    return ",".join(parts)


def render_segment(spec, src, seg, W, H, has_a, out, vol, crf):
    lf, _ = layout_filter(zoomed(spec, seg.get("zoom", 1.0)), W, H)
    if seg["kind"] == "freeze":
        png = out + ".png"
        run(["ffmpeg", "-y", "-v", "error", "-ss", f"{seg['a']:.3f}", "-i", src, "-frames:v", "1", png])
        run(["ffmpeg", "-y", "-v", "error", "-loop", "1", "-t", f"{seg['dur']:.3f}", "-i", png,
             "-f", "lavfi", "-t", f"{seg['dur']:.3f}", "-i", "anullsrc=r=48000:cl=stereo",
             "-filter_complex", f"{lf},fps={FPS},format=yuv420p[v]", "-map", "[v]", "-map", "1:a",
             "-c:v", "libx264", "-preset", "veryfast", "-crf", str(crf), "-c:a", "aac", "-b:a", "192k",
             "-ar", "48000", "-shortest", out])
        return
    length = seg["b"] - seg["a"]
    sp = seg["speed"]
    vf = f"{lf},setpts=(PTS-STARTPTS)/{sp},fps={FPS},format=yuv420p[v]"
    if has_a:
        af = f"[0:a]asetpts=PTS-STARTPTS,aresample=48000,volume={vol}" + ("" if sp == 1 else "," + atempo(sp)) + "[a]"
        ainp, amap = [], "[a]"
    else:
        af, ainp, amap = "", ["-f", "lavfi", "-i", "anullsrc=r=48000:cl=stereo"], "1:a"
    fc = vf + (";" + af if af else "")
    run(["ffmpeg", "-y", "-v", "error", "-ss", f"{seg['a']:.3f}", "-t", f"{length:.3f}", "-i", src, *ainp,
         "-filter_complex", fc, "-map", "[v]", "-map", amap, "-t", f"{length / sp:.3f}",
         "-c:v", "libx264", "-preset", "veryfast", "-crf", str(crf), "-c:a", "aac", "-b:a", "192k",
         "-ar", "48000", "-ac", "2", out])


# ---------- text cards ----------
def wrap(draw, text, font, maxw):
    words, lines, cur = text.split(), [], ""
    for w in words:
        t = (cur + " " + w).strip()
        if draw.textlength(t, font=font) <= maxw or not cur:
            cur = t
        else:
            lines.append(cur)
            cur = w
    if cur:
        lines.append(cur)
    return lines


def text_png(path, W, H, text, y, size, fontfile, align="center", stroke=None, maxw=0.88, x=None, fill="white", cx=None):
    img = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    font = ImageFont.truetype(fontfile, size) if fontfile else ImageFont.load_default()
    stroke = stroke if stroke is not None else max(3, size // 9)
    lines = wrap(d, text, font, W * maxw)
    lh = int(size * 1.12)
    for i, ln in enumerate(lines):
        w = d.textlength(ln, font=font)
        xx = (cx if cx is not None else W / 2) - w / 2 if align == "center" else (x if x is not None else W * 0.05)
        d.text((xx, y + i * lh), ln, font=font, fill=fill, stroke_width=stroke, stroke_fill="black")
    img.save(path)
    return y + len(lines) * lh


def main():
    args = sys.argv[1:]
    if not args:
        die(__doc__)
    spec_path = Path(args[0]).resolve()
    draft, loud = "--draft" in args, "--no-loudnorm" not in args
    spec = json.loads(spec_path.read_text(encoding="utf-8"))
    base = spec_path.parent
    src = str((base / spec["src"]).resolve())
    out = (base / spec.get("out", "renders/out.mp4")).resolve()
    out.parent.mkdir(parents=True, exist_ok=True)
    W, H = spec.get("size", [1080, 1920])
    if draft:
        W, H = W // 2, H // 2
    crf = 26 if draft else 18
    sw, sh, dur, has_a = probe(src)
    for k in ("facecam", "game"):
        r = spec.get(k)
        if r and (r[0] + r[2] > sw or r[1] + r[3] > sh):
            die(f"{k} crop {r} is outside the {sw}x{sh} source")
    segs, total = build_segments(spec, dur)
    tmp = Path(tempfile.mkdtemp(prefix="clip_"))
    try:
        parts = []
        for i, s in enumerate(segs):
            p = str(tmp / f"seg{i:02d}.mp4")
            render_segment(spec, src, s, W, H, has_a, p, spec.get("volume", 1.0), crf)
            parts.append(p)
        lst = tmp / "list.txt"
        lst.write_text("".join(f"file '{p}'\n" for p in parts))
        body = str(tmp / "body.mp4")
        run(["ffmpeg", "-y", "-v", "error", "-f", "concat", "-safe", "0", "-i", str(lst), "-c", "copy", body])

        # text overlays
        _, top = layout_filter(spec, W, H)
        fontfile = font_path(spec.get("lang_font", "latin"))
        k = min(W, H) / 1080
        vert = H > W
        g_top = top if top else (int(H * 0.16) if vert else int(H * 0.06))
        overlays = []  # (png, t0, t1)
        if banner_h(spec, H):
            p = str(tmp / "banner.png")
            banner_png(p, W, H, spec, fontfile)
            overlays.append((p, 0, total))
        credit = spec.get("credit", "")
        if spec.get("handle"):
            credit = f"{credit}  |  {spec['handle']}" if credit else spec["handle"]
        if credit:
            p = str(tmp / "credit.png")
            text_png(p, W, H, credit, g_top + int(18 * k), int(34 * k), fontfile, align="left", stroke=3,
                     x=int(28 * k))
            overlays.append((p, 0, total))
        hook_y = g_top + int(80 * k)
        pip = spec.get("layout") == "pip"
        hk = dict(maxw=0.62, cx=W * 0.36) if pip else {}
        teaser_end = next((s["o1"] for s in segs if s["part"] == "teaser"), 0.0)
        if spec.get("teaser_text") and teaser_end:
            p = str(tmp / "hook.png")
            text_png(p, W, H, spec["teaser_text"].upper(), hook_y, int(92 * k), fontfile, **hk)
            overlays.append((p, 0, teaser_end))
        for i, pl in enumerate(spec.get("punchlines", [])):
            spans = map_range(segs, pl["start"], pl["end"], parts=("main",))
            if not spans:
                print(f"warning: punchline '{pl['text']}' is outside the keep ranges - skipped")
            for o0, o1 in spans:
                p = str(tmp / f"pl{i}.png")
                text_png(p, W, H, pl["text"].upper(), hook_y, int(92 * k), fontfile, **hk)
                overlays.append((p, o0, o1))
        sub_y = int(H * (0.66 if vert else 0.80))
        if spec.get("subtitles"):
            for i, (a, b, txt) in enumerate(parse_srt(base / spec["subtitles"])):
                for j, (o0, o1) in enumerate(map_range(segs, a, b)):
                    p = str(tmp / f"sub{i}_{j}.png")
                    text_png(p, W, H, txt, sub_y, int(60 * k), fontfile, stroke=max(3, int(6 * k)), maxw=0.84)
                    overlays.append((p, o0, o1))

        inputs, chains, last = ["-i", body], [], "[0:v]"
        for i, (p, a, b) in enumerate(overlays):
            inputs += ["-i", p]
            chains.append(f"{last}[{i + 1}:v]overlay=0:0:enable='between(t,{a:.3f},{b:.3f})'[v{i}]")
            last = f"[v{i}]"
        flash = spec.get("flash", True) and teaser_end > 0
        aud = "[0:a]"
        if flash:
            T0 = teaser_end
            n = len(overlays) + 1
            inputs += ["-f", "lavfi", "-t", "0.35", "-i", f"color=white:s={W}x{H}:r={FPS}",
                       "-f", "lavfi", "-t", "0.5", "-i", "anoisesrc=color=pink:r=48000:a=0.6"]
            chains.append(f"[{n}:v]format=rgba,fade=out:st=0.04:d=0.3:alpha=1,setpts=PTS+{T0:.3f}/TB[fl]")
            chains.append(f"{last}[fl]overlay=0:0:eof_action=pass[vf]")
            last = "[vf]"
            d_ms = max(0, int((T0 - 0.25) * 1000))
            chains.append(f"[{n + 1}:a]highpass=f=400,lowpass=f=6000,afade=t=in:d=0.25,afade=t=out:st=0.25:d=0.25,"
                          f"aformat=channel_layouts=stereo,adelay={d_ms}|{d_ms},volume=0.9[wh]")
            chains.append("[0:a][wh]amix=inputs=2:duration=first:dropout_transition=0,volume=2[am]")
            aud = "[am]"
        if loud:
            chains.append(f"{aud}loudnorm=I=-14:TP=-1.5:LRA=11,aresample=48000[aout]")
        else:
            chains.append(f"{aud}anull[aout]")
        chains.append(f"{last}format=yuv420p[vout]")
        run(["ffmpeg", "-y", "-v", "error", *inputs, "-filter_complex", ";".join(chains),
             "-map", "[vout]", "-map", "[aout]", "-r", str(FPS), "-c:v", "libx264", "-preset", "veryfast",
             "-crf", str(crf + 2), "-c:a", "aac", "-b:a", "192k", "-movflags", "+faststart",
             "-t", f"{total:.3f}", str(out)])
    finally:
        shutil.rmtree(tmp, ignore_errors=True)

    tl = {"total": round(total, 2), "teaser_end": round(teaser_end, 2),
          "segments": [{k2: (round(v, 3) if isinstance(v, float) else v) for k2, v in s.items()} for s in segs]}
    Path(str(out) + ".timeline.json").write_text(json.dumps(tl, indent=1))
    print(f"wrote {out}  ({total:.1f} s, {W}x{H})")
    if H > W and not (12 <= total <= 20):
        print(f"warning: {total:.1f} s - Theft Talk clip Shorts should be 12-20 s (12-16 preferred)")


if __name__ == "__main__":
    main()
