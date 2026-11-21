---
name: "channel-studio"
description: "Use when making any video or Short for Theft Talk or the user's other channels and the format isn't already fixed: GTA/game news, streamer clip Shorts (faceless clipping page), clip compilations, a story or explainer, a cinematic film, a long-form video, or \"what should we post to grow\"."
---

# Channel Studio: four engines, one channel

One front door for every video and Short. First ask what to create (below), pick the engine by what the video is
for, then follow that engine's own skill exactly. This skill adds the question, the picker, the cinematic engine's
setup, the streamer clip engine (section 5), and the bridges between them.

| The video | Engine | Follow |
| --- | --- | --- |
| Today's news in 30-40 s (date, price, size, trailer, delay) | **News stills** | `gameplay-shorts` skill |
| A story, what-if, heist, map/history angle as a cartoon Short | **Animated styles** | `faceless-shorts-plus` skill |
| A deep dive with evidence: timeline, leak history, "everything we know", a real-world story behind the game, 60 s to 6 min | **Cinematic film** | sections 1-4 below |
| The user's own recorded gameplay | Footage cut | `gameplay-shorts` section 1b |
| A funny streamer moment (GTA 6 or any game) as a 12-20 s Short, facecam on top, text only | **Streamer clips** | section 5 below |
| A funniest-moments / best-of long video built from streamer clips | **Clip compile** | section 5f below |

If two fit, choose the faster one for news and the cinematic one for anything that will still be true next month.
All render rules in the `video-making` skill apply to every engine (look at full-size frames first; one full render).

## Start: ask what to create (every time, before any research)
Ask with AskUserQuestion (plain text if it is missing) unless the user already said what they want:
1. **What to make**: News Short (stills) · Streamer clip Short (section 5) · Animated story Short · Cinematic long
   video · Clip compilation long video (section 5f) · Own gameplay cut. Recommend the one that fits today
   (a launch week favours streamer clips; a real update favours a news Short).
2. **Topic or source**, when not obvious: a news hook, a story idea, or for clips "you pick the funniest moment" vs
   a Twitch/YouTube clip link the user gives.
3. **Language**: Hindi voice (default for narrated engines) / English twin. For clip Shorts: English or Hinglish
   (Latin script) on-screen text; clip Shorts have no voiceover.
4. **After it's made**: upload to YouTube now / schedule / just send me the file.
Then follow the chosen engine. Show the plan, wait for "Build it?", build, show the cut, and upload only after
the user confirms title, visibility and time (faceless-shorts-plus publishing rules).

## 0. The weekly mix (default plan when the user asks what to post)
- News Short the same day a real update lands (news stills). Never invent news to fill a day.
- In a launch or big-update week: 1-3 streamer clip Shorts a day (section 5), after the first 3 are approved.
- 2-3 animated story Shorts a week, as a numbered series (`series.py check` must say ORIGINALITY OK).
- One cinematic film a week: 16:9, 2-5 min, on an evergreen question. Then cut 2-3 vertical teasers from its
  best beats, each ending by pointing at the full film. Shorts bring the viewers, the film keeps them.
- Every video: hook in the first second, one idea only, last line loops or points to the next video.
- Hindi first (`hm_psi`), English twin (`am_michael`) declared as a twin. Voice natural, never pitched down.
- These are working rules, not guarantees. After each week ask the user for the YouTube Studio numbers (views,
  average % viewed, subscribers gained per video) and shift the mix toward what held viewers.

## 1. Cinematic engine: install or refresh
```bash
if [ -d ~/.cinematic-skill/.git ]; then git -C ~/.cinematic-skill pull -q --ff-only;
else git clone -q --depth 1 https://github.com/Moh4696/cinematic-skill.git ~/.cinematic-skill; fi
C=~/.cinematic-skill/skills/cinematic-film
python3 -m pip install -q skia-python numpy pillow scipy   # add --break-system-packages if pip refuses
python3 $C/scripts/check_setup.py                          # must end with: ready
```
**Hindi patch (run once after every install or pull).** The scripts count only a-z letters, so Hindi lines crash
`split_takes.py` and every `doc.W()` lands at the line start. Work from a patched copy:
```bash
rm -rf ~/.cinematic-hi && cp -r $C ~/.cinematic-hi && C=~/.cinematic-hi
sed -i 's/\[^A-Za-z\]/[^A-Za-z\\u0900-\\u097f]/g; s/\[^a-z\]/[^a-z\\u0900-\\u097f]/g' \
  $C/scripts/split_takes.py $C/scripts/make_beats.py $C/scripts/engine.py $C/scripts/captions.py
```
After this, `doc.W(line, "हिंदी शब्द")` works on the Devanagari `spoken` text.

Read `$C/SKILL.md` in full, then `$C/references/story.md` and `film.md` before writing a scene. Follow its
workflow and its four approval gates. Everything below overrides it only where the two differ.
Projects live in `~/faceless-shorts/<name>/` like the other engines: `python3 $C/scripts/new_project.py <path>`,
then `python3 $C/scripts/get_fonts.py --project <path>`. Output paths (`--out out/x.mp4`) are inside the project.

## 2. Bridges (what the cinematic repo does not know about this channel)

**Voice: Kokoro, not the scratch voice.** Save this as `<project>/kokoro_take.py` and record takes with the
PLUS toolkit's Python (`PY = ~/.faceless-shorts/skill-plus/scripts/py`, it has Kokoro):
```python
import sys, numpy as np, soundfile as sf
from kokoro import KPipeline
txt, out, voice, lang, speed = sys.argv[1], sys.argv[2], sys.argv[3], sys.argv[4], float(sys.argv[5])
pipe = KPipeline(lang_code=lang)                       # 'h' Hindi, 'a' American English
gap, parts = np.zeros(int(24000 * 0.65), np.float32), []
for para in [p.strip() for p in open(txt, encoding="utf-8").read().split("\n\n") if p.strip()]:
    parts += [np.asarray(a, np.float32) for _, _, a in pipe(para, voice=voice, speed=speed)] + [gap]
sf.write(out, np.concatenate(parts), 24000)            # the 0.65 s gaps are where split_takes.py cuts
```
```bash
python3 $C/scripts/tts_say.py --project <p> --cmd "$PY <p>/kokoro_take.py {txt} {out} hm_psi h 1.1"
python3 $C/scripts/split_takes.py --project <p> && python3 $C/scripts/build_narration.py --project <p>
```
In a cloud session (no PLUS toolkit, Hugging Face blocked): `pip install kokoro-onnx soundfile`, download
`kokoro-v1.0.onnx` and `voices-v1.0.bin` from
`https://github.com/thewh1teagle/kokoro-onnx/releases/download/model-files-v1.0/`, and in `kokoro_take.py` use
`from kokoro_onnx import Kokoro; k = Kokoro(onnx, voices); a, sr = k.create(para, voice=voice, speed=speed, lang="hi")`
(`lang="en-us"` for English) with plain `python3`.
English twin: `am_michael a 1.08`. If the Kokoro import fails, open `~/.faceless-shorts/skill-plus/scripts/voice.py`,
see how it calls Kokoro and its `natural` finish, and mirror that. Listen to every line `split_takes.py` flags.
In `script.json`, Hindi `spoken` is Devanagari with numbers written as words.

**Hindi on screen.** The engine draws text one letter at a time, which breaks Devanagari. Per project:
download Noto Sans Devanagari to `<project>/fonts/deva.ttf`
(`https://raw.githubusercontent.com/google/fonts/main/ofl/notosansdevanagari/NotoSansDevanagari%5Bwdth%2Cwght%5D.ttf`),
save the helper below as `<project>/hindi.py`, and put `import hindi` as the first import in `scene.py`.
```python
import pathlib, skia, engine
from skia import textlayout as tl
_TF = skia.Typeface.MakeFromFile(str(pathlib.Path(__file__).parent / "fonts" / "deva.ttf"))
_FC = tl.FontCollection(); _P = tl.TypefaceFontProvider(); _P.registerTypeface(_TF, "Deva")
_FC.setDefaultFontManager(_P)
_draw, _width = engine.draw_text, engine.text_width

def _para(text, size, paint):
    st = tl.TextStyle(); st.setFontFamilies(["Deva"]); st.setFontSize(size)
    st.setFontStyle(skia.FontStyle.Bold()); st.setForegroundPaint(paint)
    b = tl.ParagraphBuilder(tl.ParagraphStyle(), _FC, skia.Unicodes.ICU.Make())
    b.pushStyle(st); b.addText(text); p = b.Build(); p.layout(1e6)
    return p

def _hindi(text):
    return any("ऀ" <= ch <= "ॿ" for ch in text)

def text_width(res, text, size, font="serif", track=0.0):
    return _para(text, size, skia.Paint()).LongestLine if _hindi(text) else _width(res, text, size, font, track)

def draw_text(c, res, text, x, y, size, font="serif", rgb=engine.CREAM, a=1.0, track=0.0, align="left", reveal=None):
    if not _hindi(text):
        return _draw(c, res, text, x, y, size, font, rgb, a, track, align, reveal)
    p = _para(text, size, engine.paint(rgb, a)); w = p.LongestLine
    x0 = x - w / 2 if align == "center" else x - w if align == "right" else x
    top = y - p.AlphabeticBaseline
    c.save()
    if reveal is not None:      # type-on becomes a left-to-right wipe
        c.clipRect(skia.Rect.MakeXYWH(x0, top, w * min(1.0, reveal / max(1, len(text))), p.Height))
    p.paint(c, x0, top); c.restore()
    return w

engine.draw_text, engine.text_width = draw_text, text_width
```
Look at a full-size still of every Hindi label (matras attached, no dotted circles, nothing cut off).

**Captions.** `burn_captions.py` cannot shape Hindi. For Hindi films: put the keyword of each line on screen as
type (it lands on the spoken word anyway) and deliver `burn_captions.py --srt-only` as the YouTube subtitle file.
English twins can use `--style highlighter`. Captions take the bottom 26%: keep numbers above it.

**Vertical (teasers and cinematic Shorts).** Render with `--size 1080x1920` (draft `540x960`). The frame shows
`3840 / zoom` world units across and `6827 / zoom` down, so a landscape layout comes out tiny: stack clusters top
to bottom, keep any card under about 3000 units wide, use zoom 0.6 or closer on a hero. Every moment needs something on screen: when the camera reaches a cluster before its number is spoken, add a
small label that appears at the line start (the frame sheet of the draft shows the empty seconds).
The `night` look's grain makes huge files: for upload re-encode with `-crf 21` (about 75 MB for 43 s at 1080x1920).
A teaser is its own
scene file laid out vertically, not a crop of the 16:9 film. Long-form: `--size 2560x1440`; 4K only when asked,
and say the render time first.

**Look for Theft Talk.** `night` look, big type, counters, routes, cards, neon accent colours matching the news
stills, handle `@thefttalk` on the closing frame.

## 3. Images and facts (stricter than the cinematic repo)
- Never Rockstar logos, characters, key art, trailer frames or screenshots from the web, and no AI images imitating
  the game. Never ask the user for screenshots.
- Allowed: code-drawn cards, numbers, timelines and maps; `fetch_commons.py` photos of real places and real
  history with their credits (hand over `credits.md`); the user's own gameplay only if they offer it.
- A document drawn in code is labelled a recreation and quotes only words that were really published.
- Every number and date is searched the same day and listed in `fact_notes` with its source. Rumours are labelled
  as rumours on screen and in the voice. Countdowns count from the publish date.

## 4. Build order for a cinematic film
1. Plan on one screen (title, lines, hero per line, facts and sources), wait for "Build it?".
2. `script.json` then `make_beats.py`; fix lints (Gate: user approves beats and facts).
3. Kokoro takes, split, build narration. 4. `prep_assets.py` (and `make_map.py` if the story travels).
5. `scene.py`; `render.py --probe` one still per line, look at all of them (Gate: show opening stills).
6. Draft of the first 30 s at 1280x720 or 540x960 (Gate: user watches).
7. `render.py --cues`, `build_sfx.py`, `mix_soundtrack.py`, full render with `--audio audio/mix.m4a`.
8. Deliver like the other engines: MP4, thumbnail via `thumb.py`, title, description, 5-8 hashtags, SRT,
   credits. Uploading follows the faceless-shorts-plus publishing rules: only when asked and confirmed.
   From a cloud session the Drive connector takes at most about 3 MB per file, so a video cannot be saved to
   Drive from there: send the file to the user, ask them to put it in the Drive folder "Theft Talk Videos",
   then post it from Drive with Zapier.

## 5. Streamer clip engine (faceless clipping page, adapted from Nate Herk's Grok Bot guide)
A 12-20 s vertical Short of a real streamer's funny moment: facecam on top, gameplay below, our own hook and
punchline text, burned-in subtitles, one comedic edit, credit on screen and in the description. No voiceover.
**The edit is the product**: a plain repost is unoriginal content on YouTube, TikTok and Instagram and gets no reach.

### 5a. Toolkit
Scripts live in Drive: `Theft Talk Skill/theft-talk-clipper.zip` (find it with the Drive connector, download,
unzip to `~/.theft-talk/clipper`). `CL=~/.theft-talk/clipper/scripts`. Needs ffmpeg, Python 3, Pillow, yt-dlp
(`pip install yt-dlp`). Run on the user's computer (device_bash) when connected, else in the cloud shell.
- `clip.py spec.json [--draft]` renders one clip from a JSON spec (fields in its docstring; all times are source
  seconds, it maps them onto the output timeline and writes `<out>.timeline.json`).
- `sheet.py scout <video>` contact sheet (frame every 2 s, timestamped) · `sheet.py frame <video> <t> --grid` one
  full frame with a pixel grid to read crop boxes · `sheet.py qa <render>` hook / flash / payoff / last frames.
- `scout_twitch.py "Grand Theft Auto VI" --hours 24` top clips via Twitch Helix (needs TWITCH_CLIENT_ID and
  TWITCH_CLIENT_SECRET as env vars, never printed).
- `templates/` scoreboard.csv, log.md, learning.md, experiments.md, takedowns.md. Keep the live copies in
  `~/faceless-shorts/clips/` and a copy in the Drive folder "Theft Talk Skill/tracking".
**Network**: twitch.tv, gql.twitch.tv, api.twitch.tv, id.twitch.tv and the clip CDN (*.twitchcdn.net) must be on
the allowed domains (claude.ai Settings > Capabilities) for scouting and yt-dlp downloads. If they are blocked,
scout in a browser (Twitch category > Clips > last 24 h, or YouTube search) and ask the user to drop the source
MP4 into the Drive folder "Theft Talk Clips/inbox", or attach it. Never route around a blocked site.

### 5b. Scout, verify, dedupe (expect to reject 90%)
1. Pull the top clips of the last 3-24 h, English (or Hindi streamers for the Indian audience), sorted by views.
   Check YouTube Shorts / TikTok search ("gta 6 funny", "gta 6 cops", "gta 6 npc") for what is trending today.
2. Never trust titles: `sheet.py scout` every candidate and look. Reject: no real facecam or a tiny one, VTubers,
   anything sexual, animal harm, slurs, story spoilers or endings, leaks, cheats or exploits.
3. Pick: a visible facecam reaction to genuinely funny chaos with a clear payoff. Best themes: instant karma (brag,
   then disaster within 3 s), NPCs or cops fighting back, Lucia or Jason moments, "called it", life-sim irony,
   playful glitches, wildlife winning. Mid-size streamers' unique moments beat big-streamer moments everyone has.
4. **Verify it's GTA 6**: the GTA 6 category is full of GTA V. Need all three: created within ~24 h (and after
   launch in that region), a saved proof frame with a game-only cue (new HUD, Lucia/Jason, Vice City skyline, new
   police livery), and context (launch overlay, "first time" title). Save the proof frame; cite it in log.md.
5. **Dedupe before cutting**: search YouTube Shorts, TikTok and X for the moment; 3+ pages already posted it ->
   skip or find a clearly different angle.
6. **Send test**: write who a viewer would send it to and what they'd type ("bro this is you"). No friend, no post.
7. **Rights**: the clip belongs to the streamer. Credit them on screen and in the description, never take credit,
   prefer streamers who invite clipping (many say so in their panels or run clipping programs), take a video
   down the same day if the streamer or a claim asks, and log it in takedowns.md. Transformed clips with credit
   are normal practice but not a licence: tell the user once that claims or strikes are possible.

### 5c. Download, crop, subtitle
- `yt-dlp -o source.mp4 "<FULL clip url from the API or page>"` (truncated URLs fail).
- `sheet.py frame source.mp4 3 --grid` -> read `facecam` [x,y,w,h] (inside its border so the face fills the
  panel) and `game` [x,y,w,h] (no chat, no burned-in captions, no cam, no watermarks). No facecam -> `"layout":"fit"`.
- Subtitles: hand-time an SRT in source seconds. Order: the streamer's own burned-in captions (shift ~0.2 s
  earlier), else listen and transcribe by hand, Whisper only with every word proofread. **Never guess words**;
  if unclear, leave it out. Read in-game captions first so an NPC's line never goes in the streamer's mouth.

### 5d. The edit (payoff-first formula)
`[TEASER 2-4 s] -> [WHITE FLASH + WHOOSH] -> [SETUP 3-6 s] -> [ESCALATION] -> [PAYOFF at 70-85%] ->
[REACTION HOLD 0.5-1.5 s + PUNCHLINE] -> hard cut that loops into the teaser`
- Teaser = the funniest moment, long enough not to cut mid-word or mid-action, from a different part than where
  the payoff plays (tease the end, play from the setup; 8+ s of new footage before the payoff).
- One comedic edit only: `slowmo` 0.35-0.5x or `freeze` 0.5-1 s on the funniest frame. No zoom on stack layouts.
- Keep the real laugh audible on the reaction hold; no music over it. Length 12-20 s (12-16 preferred).
- **Text**: adds context, never describes. Banned: "STREAMER DOES X". Hooks like "GTA 6 COPS DON'T DO ROLEPLAY",
  "HE PROMISED CHAT NO MORE CRASHING"; punchlines like "INSURANCE: DENIED", "GRANDMA DOWN". Search keyword in frame
  one (GTA 6, Lucia, Jason, Vice City, streamer name). ALL CAPS only in the hook/punchline, white with black
  outline, in the gameplay area, never over the face, no emoji in burned text, punchlines outside the teaser.
- If the clip ends on a black loading screen after WASTED, end before it and use `end_freeze` on the WASTED frame.
- Render: `clip.py spec.json --draft`, then `sheet.py qa` and LOOK at every QA frame full size (hook, flash, payoff,
  last; subtitles within ~0.3 s; no foreign watermark, chat or viewer counter; text off the face). Then final
  `clip.py spec.json` (1080x1920, 30 fps, loudness -14 LUFS).

### 5e. Title, description, posting (YouTube first)
- Title: 1-6 word joke in a friend's voice with the search keyword ("day one and lucia already has a record"),
  sentence case, no question at the end, at most one emoji, never "official", "leak", "early access",
  "free copy", "giveaway"; never repeat a title within 7 days.
- Description: `Credit: @streamer (Twitch) <clip link>` first line, one line of context, then 3-5 hashtags
  (#gta6 #<streamer> #<specific> #gaming #shorts). Pinned comment: one honest question viewers can answer about
  themselves. Never imply we're Rockstar.
- Cadence: the first 3 clip Shorts are approved by the user one by one (file + title). Then up to 3-5 a day,
  at least 2.5 h apart, filling the hours when India, the Gulf and the US are awake; never in bursts.
- Upload with the faceless-shorts-plus publishing rules (Zapier YouTube, private + publish_at to schedule).
- Log every post in log.md and a row in scoreboard.csv; read stats at 2 h, 24 h, 72 h from YouTube Studio (ask
  the user for them, or read them in the browser if they ask). Judge on ratios: avg % viewed, likes per view,
  shares per view, subs per 1,000 views; never judge a format in under 24 h.
- Stuck rule: under 20 views after 1 h = stuck. Check YouTube Studio for a claim or restriction before anything
  else; repost only as a fresh cut (new teaser, trim, hook, title), never the same file. Never post within 2 h
  of a channel profile change.
- Momentum: a post that beats 3x the channel median gets a same-theme or same-streamer follow-up within 24 h.
- Experiments live in experiments.md: one variable per test, metric and kill condition written first.

### 5f. Clip compilation (long video, 16:9)
For "funniest GTA 6 launch moments" style videos: render each clip with `"size":[1920,1080]` and `"layout":"pip"`
(gameplay full frame, facecam inset top-right) or `"full"`, same spec rules and credits per clip, then
`ffmpeg -f concat -safe 0 -i list.txt -c copy compile.mp4` (all clip.py outputs share codecs). Open with the best
moment as a 3 s cold open, 8-15 clips, credits for every streamer in the description with timestamps (chapters).
A thumbnail via `thumb.py --size long`. Cut 2-3 of its clips as vertical Shorts pointing to the full video.

### 5g. Running it as a routine (only when the user asks)
The guide's 2-hour "CEO" loop (analyze, health check, learn one question, scout, verify, cut, QA, schedule,
strategize, dashboard, clean up, report) can run as a scheduled task once Twitch access and auto-upload work.
Until the user approves the first 3 posts, nothing posts on its own. Overnight (11 PM-7 AM IST) stay quiet unless
something breaks. Never pay, sign up, upgrade, message anyone or change the channel profile without the user.
Delete raw sources once a clip is cut and scheduled; keep nothing raw older than 24 h.

## Never
Everything in the engines' Never lists, plus: post a streamer clip that is a plain repost, uncredited, unverified
(GTA V passed off as GTA 6) or one 3+ pages already posted; guess subtitle words; keep a video up after a takedown
request; ship Hindi text you have not looked at full size; crop a
16:9 film into a Short; present a rumour as confirmed; promise growth numbers.