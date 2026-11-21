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
