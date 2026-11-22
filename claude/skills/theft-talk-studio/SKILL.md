---
name: theft-talk-studio
description: Make, check and schedule GTA 6 YouTube Shorts for Ankush's channel Theft Talk (@thefttalk) end to end - scout Twitch streamer clips (side missions, girl streamers, big streamers, curiosity), cut them with the top GTA 6 title banner and punch-in edit, QA, host and upload as scheduled private Shorts; also Hindi side-mission guide Shorts. Use whenever Ankush asks to make a Short, find clips, upload, schedule, check stats or "do today's Shorts".
---

# Theft Talk Studio

Ankush runs @thefttalk (channel ID `UCgppTvPhWdNG-scO-fQPyfA`), a GTA 6 Shorts channel. He said "you decide, you are master": pick clips, build, check and schedule like a skilled YouTube creator whose goal is viral Shorts. Every upload is scheduled private + publish_at, never instantly public; he vetoes by keeping it private.

## 0. Pick the job

| Ankush says | Do |
| --- | --- |
| "make a Short", a streamer name, a Twitch clip link | Sections 1-5 (one clip Short) |
| "do today's Shorts" | Section 6 (the daily batch) |
| "upload this / schedule it" | Section 5, or the Zapier skill `theft-talk-upload-short` |
| "how are we doing", "stats", "what's trending" | Zapier skill `theft-talk-channel-stats` |
| "move / cancel / fix the description" | Zapier skill `theft-talk-reschedule` |
| "Hindi guide", a side-mission name | Section 7 |

Zapier skills live in Ankush's Zapier account: read them with `get_zapier_skill` (uri `skill://...` from `list_zapier_skills`) and follow them.

## 1. Tools and where things live

- **Ankush's Mac** (via the Claude desktop app bridge): Desktop Commander `start_process` / `read_file` / `write_file`. Render tools in `~/faceless-shorts/tt-tools` (git clone of `ankush2001/New-Project`, branch `thefttalk-tools`; `git pull` first). Scripts: `clipper/scripts/clip.py`, `sheet.py`, `news_stills.py`. Work folders `~/faceless-shorts/clipsYYYYMMDD/`, bank `~/faceless-shorts/bank/`. gh/git on the Mac is logged in as ankush2001.
- **Built-in browser** on the Mac (`Claude_Browser` tools; load the built-in-browser skill). Twitch is blocked in cloud shells, so scout and grab clip video URLs here.
- **Zapier YouTube** (selected_api `YouTubeV4CLIAPI`): upload_video, Make API GET Request (`youtube_make_api_get_request`), Make API Mutating Request. Put parameters in the `querystring` dict, never in the URL; fail_on_errors "false".
- **Tracking** on branch `thefttalk-tools`: `tracking/log.md`, `scoreboard.csv`, `learning.md`, `bank.md`, `missions.md`. Read them first so you never reuse a clip; append every upload.
- If the Mac or browser cannot be reached: say so; you can still do stats, reschedules and (in a cloud shell with ffmpeg) re-uploads of already-hosted files.

## 2. What wins (data as of 23 Nov 2026; update from `tracking/learning.md`)

- Our best: English streamer clips with one clear funny payoff (Jerma985 gator 1,483 views, 76% viewed; caseoh 496; Stormfall33 boat 451 after sitting at 5 views for 11 h - never judge before 24 h). Hindi voice Shorts get 4-60 views; Hinglish titles and long videos 1-2. About 95% of views are US.
- Viral GTA 6 Shorts in launch week: curiosity/discovery (Bigfoot in GTA 6 8.0M, leaving the map 4.4M, GTA 6 vs RDR2 animals 4.9M, physics comparison 4.8M) and big streamers named in a full-sentence title (Kai Cenat/Rakai 5.1M, Speed 3.0M, Jynxzi 2.7M). Side-mission streamer clips by other pages only get 1K-35K: nobody owns side missions yet. Female streamers are under-covered.
- Focus order: SIDE-MISSION MOMENTS, GIRL STREAMERS, BIG STREAMERS (IShowSpeed, Kai Cenat, Jynxzi, CaseOh, Lacy), CURIOSITY ("what happens if", secrets, easter eggs, Bigfoot/Skunk Ape, GTA 6 vs GTA 5). Plain driving crashes are a last resort.
- Momentum: any Short above 3x the channel median gets a same-streamer or same-theme follow-up within 24 h.

## 3. Scout (expect to reject 90%)

1. Browser: `twitch.tv/directory/category/grand-theft-auto-vi/clips?range=24hr` (scroll with real mouse scrolls; JS scrolling does not load more), then `twitch.tv/<streamer>/clips?range=24hr` for ishowspeed, kaicenat, jynxzi, caseoh_, lacy, jerma985, and female streamers (dahlia, jill, jeanobean0, marzzzzy, valkyrae, emiru, fanfan and whoever the category shows). Look at 50+ clips. List cards with JS: each `a[href*="/clip/"]` and its card's innerText (title, streamer, length, views, age).
2. Side missions: Strangers & Freaks givers Shirley, Kirk (Skunk Ape), Kyle ("Red Hulk"), Bret, Billy, Yago, Andy, Tyrone, Eddie, Pilot Pete; the bear rescue; Return Tootsie to the farmer; robberies; street and dirt bike races; fishing; police impound jobs. Read the mission name from the on-screen objective or two sources; never guess.
3. Grab the video: on the clip page `document.querySelector('video').currentSrc`. Download on the Mac in one script: `curl -sL -o ~/faceless-shorts/clipsYYYYMMDD/<name>.mp4 '<url>' &` per clip, `wait`, then `python3 ~/faceless-shorts/tt-tools/clipper/scripts/sheet.py scout <file>` and LOOK at each `<name>_sheet.jpg` (frame every 2 s). For timing use a dense sheet: `ffmpeg -i x.mp4 -vf "fps=2,scale=384:-1,tile=6x7" -frames:v 1 x_dense.jpg`.
4. Reject: no facecam or a tiny one, VTuber/avatar cams, anything sexual or sexualised (with female streamers too: no thirst framing, no comments on bodies), violence against people (NPCs hit, bodies, gasoline/fire on people), animal cruelty, slurs (also in burned captions), main-story missions, cutscenes, chapter endings or late-game reveals, leaks, game-crash screens with key art, heavy chat overlays you cannot crop out.
5. Verify it is GTA 6 (new HUD, Lucia/Jason, Leonida/Vice City, GTA 6 category, made in the last ~24 h). Dedupe against `tracking/log.md`.
6. Send test: who would a viewer send it to, and what would they type? No friend, no post.

## 4. Cut (clip.py on the Mac)

1. `sheet.py frame <file> 3 --grid` and read crops in source pixels: `facecam` [x,y,w,h] tight on the face (the top panel is about 1.4:1), `game` [x,y,w,h] about 0.94:1 with no chat, cam, stream timer, minimap or burned-in captions.
2. Spec (copy and edit; times are SOURCE seconds):
```json
{"src":"jerma_pool.mp4","out":"renders/TT-0NN.mp4",
 "credit":"Jerma985 (Twitch)","handle":"@thefttalk",
 "banner":{"text":"Jerma tried to high dive into a pool from a skyscraper","badge":"GTA 6","color":"cyan"},
 "layout":"stack","facecam":[0,525,270,270],"game":[520,0,900,960],"split":0.40,
 "teaser":{"start":16.8,"end":18.8},
 "keep":[[0.2,2.4],[5.6,8.0],[11.5,18.6]],
 "punch":{"start":13.9,"end":15.2,"zoom":1.3},
 "punchlines":[{"start":5.8,"end":8.0,"text":"PERFECT AIM SO FAR..."},
               {"start":15.4,"end":18.6,"text":"10/10 DIVE. 0/10 SURVIVAL"}],
 "subtitles":"TT-0NN.srt"}
```
   - `banner`: the top title bar for the whole video, our own neon "GTA 6" badge (never Rockstar's logo or art). Text = full sentence: streamer + what happens (+ mission name). Colors pink, cyan, gold, green, red.
   - Teaser = the funniest 1-2 s first, from a different moment than the full play; then a white flash.
   - `punch`: the one comedic edit, a hard 1.25-1.35x punch-in for 1-1.5 s on the payoff. No slow-mo.
   - Punchlines: ALL CAPS, add context, never describe ("CHAT WAS RIGHT", "THERE WAS A SECOND TRUCK"), in the gameplay area, never over the face.
   - Subtitles only from words you can hear or read (the streamer's own burned-in captions count; check it's not an NPC line). Never guess.
   - Length 12-17 s. If it ends on a black loading screen after WASTED, end before it.
3. `python3 clip.py spec.json --draft`, `python3 sheet.py qa renders/TT-0NN.mp4`, LOOK at the QA sheet (hook, flash, payoff, last), fix, then the final render without `--draft` and QA again.

## 5. Host and upload

1. Host from the Mac: copy finals into a fresh folder, `git init`, `git checkout --orphan media-YYYYMMDD`, commit, `git push https://github.com/ankush2001/New-Project.git media-YYYYMMDD`. Link: `https://raw.githubusercontent.com/ankush2001/New-Project/media-YYYYMMDD/TT-0NN.mp4` (check it returns 200).
2. Upload with the Zapier skill `theft-talk-upload-short` (title, description template, tags, slot rules, UTC conversion, verification are all in it). Slots IST: 19:30 girl streamer, 21:30 Hindi, 23:30 side mission, 05:30 strongest; 2 h apart.
3. Limits: about 5-6 uploads per rolling 24 h; API quota 10,000 units/day reset 13:30 IST (upload 1,600, search 100, update 50). If throttled, stop and schedule the leftovers after the reset.
4. Log: append to `tracking/log.md` (hook, title, source URL, proof, edit, link) and `scoreboard.csv` on `thefttalk-tools`; commit messages end with `Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>`. Bank good extra clips in `tracking/bank.md` (MP4 in `~/faceless-shorts/bank`, max 3 days).

## 6. The daily batch

A scheduled task "Theft Talk · daily clip Shorts" already runs every day at 14:43 IST with the full rules. When Ankush asks in a chat instead: run `theft-talk-channel-stats` (with trends), count what is already scheduled in the next 24 h, then fill the free slots with sections 3-5 (max 4 uploads), and finish with one short summary: yesterday's best/worst with views, today's titles + IST times + youtu.be links, the bank, anything skipped.

## 7. Hindi side-mission guide Short (slot 21:30 IST on days without real news)

- One side mission, 25-35 s: where to find it, how to start it, 2-3 tips, the reward. Facts only from 2 guide sites searched today that agree (KeenGamer, HoldToReset, GamesRadar, PowerPyx, AlcastHQ); if they disagree, pick another mission. Check `tracking/missions.md` (Skunk Ape done 22 Nov).
- Real news instead when there is same-day GTA 6 news from real sources; never invent news.
- Build on the Mac like `~/faceless-shorts/tt012/build.sh`: `stills.json` for `news_stills.py` (kinds big / card; Pillow there has no raqm, so avoid Devanagari conjuncts and the i-matra on stills - write TRUCK, TORCH, DRONE in English - and LOOK at `review/stills.jpg`), one line of `lines.txt` per still, voice `~/faceless-shorts/voice-test/.venv/bin/edge-tts --voice hi-IN-MadhurNeural --rate=+10%` (casual Hindi like a friend, numbers as words, never pitched down), concat, loudnorm -14.
- Title in Devanagari with the English mission name; description = numbered steps, question, `Sources: ...`, disclaimer.

## Never

Upload instantly public; reuse a clip already in the log; use Rockstar logos, key art, trailer frames or web screenshots; story spoilers; leaked footage; sexualised content; guess subtitle words or mission names; type a password or API key; create accounts; buy anything; delete YouTube videos. Credit every streamer on screen and in line 1 of the description; take a video down (set private) the same day a streamer asks.
