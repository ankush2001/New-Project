#!/usr/bin/env python3
"""build_long.py - 16:9 narrated countdown / compilation (LONG videos) from clip.py renders.

  python3 build_long.py long.json [--draft]

long.json (paths relative to it):
  out, size [1920,1080], fps 30, vbitrate "2800k" (keeps a 4-5 min video under GitHub's 100 MB)
  music      music.wav from music.py (quiet bed under cards only), music_db -20
  whisper_py path to the faster-whisper python (for auto_mute), optional
  seq: list of
    {"type":"clip","file":"renders/c8.mp4","a":0,"b":null,"auto_mute":true}   play a rendered clip (its own audio);
        auto_mute: transcribe it and silence swear words
    {"type":"card","vo":"vo/l2.wav","bg":"renders/c8.mp4","bg_t":1.0,"big":"#8","sub":"DarkViperAU"}
        narrator card: blurred still of bg at bg_t, big number + name, narrator voice + music, length = voice + 0.5 s
Writes <out> and <out>.chapters.txt (start time of every card with big text, for the description).
"""
import json, subprocess, sys, tempfile, shutil
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
import clip  # noqa: E402

SWEAR = {"fuck", "fucking", "fucked", "fucker", "motherfucker", "shit", "shitty", "bullshit", "bitch", "bitches",
         "ass", "asshole", "damn", "goddamn", "dick", "pussy", "nigga", "nigger", "cunt", "bastard", "hell"}


def run(cmd):
    r = subprocess.run(cmd, capture_output=True, text=True)
    if r.returncode:
        sys.exit("build_long.py: command failed:\n" + " ".join(map(str, cmd)) + "\n" + r.stderr[-2500:])
    return r


def dur(p):
    return float(run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", str(p)]).stdout)


def swear_ranges(wpy, f, tmp):
    run([wpy, str(Path(__file__).parent / "transcribe.py"), str(f), "--model", "small.en"])
    wj = Path(str(f).rsplit(".", 1)[0] + ".words.json")
    out = []
    for w in json.loads(wj.read_text()):
        t = w["w"].lower().strip(".,!?\"'-")
        if t in SWEAR or any(t.startswith(s) for s in ("fuck", "shit", "bitch", "nigg")):
            out.append((max(0, w["s"] - 0.08), w["e"] + 0.08))
    return out


def main():
    spec_p = Path(sys.argv[1]).resolve()
    base = spec_p.parent
    spec = json.loads(spec_p.read_text(encoding="utf-8"))
    draft = "--draft" in sys.argv
    W, H = spec.get("size", [1920, 1080])
    if draft:
        W, H = W // 2, H // 2
    fps = spec.get("fps", 30)
    music = base / spec["music"] if spec.get("music") else None
    mdb = spec.get("music_db", -20)
    anton = clip.font_path("latin")
    tmp = Path(tempfile.mkdtemp(prefix="long_"))
    parts, chapters, t_out, m_off = [], [], 0.0, 0.0
    try:
        for i, it in enumerate(spec["seq"]):
            p = tmp / f"p{i:02d}.mp4"
            if it["type"] == "clip":
                f = base / it["file"]
                a = it.get("a", 0.0)
                b = it.get("b") or dur(f)
                vol = "volume=1"
                if it.get("auto_mute") and spec.get("whisper_py"):
                    rs = [(s, e) for s, e in swear_ranges(spec["whisper_py"], f, tmp) if e > a and s < b]
                    if rs:
                        cond = "+".join(f"between(t,{s - a:.3f},{e - a:.3f})" for s, e in rs)
                        vol = f"volume='if({cond},0,1)':eval=frame"
                        print(f"  muted {len(rs)} word(s) in {it['file']}")
                run(["ffmpeg", "-y", "-v", "error", "-ss", f"{a:.3f}", "-t", f"{b - a:.3f}", "-i", str(f),
                     "-vf", f"scale={W}:{H}:force_original_aspect_ratio=decrease,pad={W}:{H}:(ow-iw)/2:(oh-ih)/2,fps={fps},format=yuv420p",
                     "-af", f"aresample=48000,aformat=channel_layouts=stereo,{vol}",
                     "-c:v", "libx264", "-preset", "veryfast", "-crf", "16", "-c:a", "aac", "-b:a", "192k", str(p)])
                L = b - a
            else:
                vo = base / it["vo"]
                L = dur(vo) + 0.5
                still = tmp / f"s{i}.png"
                run(["ffmpeg", "-y", "-v", "error", "-ss", f"{it.get('bg_t', 0.5):.3f}", "-i", str(base / it["bg"]),
                     "-frames:v", "1", "-vf", f"scale={W}:{H},boxblur=18:2,eq=brightness=-0.22:saturation=1.2", str(still)])
                txt = tmp / f"t{i}.png"
                k = H / 1080
                y = clip.text_png(str(txt), W, H, it.get("big", ""), int(H * 0.30), int(230 * k), anton,
                                  stroke=int(10 * k), fill=(255, 214, 10))
                if it.get("sub"):
                    t2 = tmp / f"u{i}.png"
                    clip.text_png(str(t2), W, H, it["sub"], y + int(10 * k), int(96 * k), anton, stroke=int(6 * k))
                else:
                    t2 = txt
                if it.get("big"):
                    chapters.append((t_out, f"{it['big']} {it.get('sub', '')}".strip()))
                fa = 0.25
                ins = ["-loop", "1", "-t", f"{L:.3f}", "-i", str(still), "-i", str(txt), "-i", str(t2), "-i", str(vo)]
                fc = (f"[0:v][1:v]overlay=0:0[a0];[a0][2:v]overlay=0:0,zoompan=z='1+0.0006*on':x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':d=1:s={W}x{H}:fps={fps},"
                      f"fade=t=in:st=0:d={fa},format=yuv420p[v];"
                      f"[3:a]aresample=48000,aformat=channel_layouts=stereo,apad,atrim=0:{L:.3f},volume=1.5[vo]")
                amap = "[vo]"
                if music:
                    ins += ["-ss", f"{m_off:.3f}", "-t", f"{L:.3f}", "-i", str(music)]
                    fc += (f";[4:a]aresample=48000,aformat=channel_layouts=stereo,volume={mdb}dB,"
                           f"afade=t=in:d=0.3,afade=t=out:st={max(0, L - 0.4):.3f}:d=0.4[mu];[vo][mu]amix=inputs=2:duration=first:normalize=0[am]")
                    amap = "[am]"
                    m_off += L
                run(["ffmpeg", "-y", "-v", "error", *ins, "-filter_complex", fc, "-map", "[v]", "-map", amap,
                     "-t", f"{L:.3f}", "-c:v", "libx264", "-preset", "veryfast", "-crf", "16", "-c:a", "aac", "-b:a", "192k", str(p)])
            parts.append(p)
            t_out += L
            print(f"{i:02d} {it['type']:4s} {L:5.1f} s  (at {t_out - L:6.1f})", flush=True)
        lst = tmp / "list.txt"
        lst.write_text("".join(f"file '{p}'\n" for p in parts))
        out = base / spec["out"]
        vb = spec.get("vbitrate", "2800k")
        run(["ffmpeg", "-y", "-v", "error", "-f", "concat", "-safe", "0", "-i", str(lst),
             "-c:v", "libx264", "-preset", "veryfast" if draft else "medium",
             *(["-crf", "26"] if draft else ["-b:v", vb, "-maxrate", vb.replace("k", "") + "k", "-bufsize", "6000k"]),
             "-r", str(fps), "-af", "loudnorm=I=-14:TP=-1.5:LRA=11", "-c:a", "aac", "-b:a", "192k",
             "-movflags", "+faststart", str(out)])
        ch = "\n".join(f"{int(t // 60)}:{int(t % 60):02d} {name}" for t, name in [(0.0, "Intro")] + chapters[1:])
        Path(str(out) + ".chapters.txt").write_text(ch + "\n")
        print(f"wrote {out} ({t_out:.1f} s)\n{ch}")
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


if __name__ == "__main__":
    main()
