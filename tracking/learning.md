# Learning notes (one entry per daily run)

## 2026-11-22
- Won: English streamer clips with one wildlife/karma idea (Jerma gator 1,483 views, 76% viewed; caseoh 496). Lost: TT-008 Stormfall boat (5 views in 11 h), Hinglish clip (2), long videos (1 each); best Hindi is TT-006 price (60). No part-2 or mission Shorts yet, so no series-vs-single comparison.
- Change today: momentum on Jerma (2 follow-ups), first mission moment (dirt bike race activity, slot B), first Hindi side-mission guide (Skunk Ape) instead of news. Judge these three at 24 h against the 35-view median.
- 23 Nov 00:30 IST: Ankush asked for viral style. Switched to top title banner + punch-in (no slow-mo), streamer-name sentence titles, story + question descriptions; focus side missions, girl streamers, big streamers, curiosity. Compare banner Shorts vs old style at 24 h.

## 2026-11-23 voice test (Ankush asked after an Instagram reel with a Hindi AI narrator)
- OmniVoice (k2-fsa, 16.8K stars, Apache-2.0, 600+ languages incl. Hindi) runs on the Mac (MPS fp16): ~10-16 s per line after the first load; same script 15.8 s vs Edge Madhur 26 s (faster storyteller pace). Tool: clipper/scripts/omni_say.py. VoxCPM2 (42.9K) is too heavy for the 8 GB Mac (float32 on MPS, ~1 h per Short on CPU). Never clone another creator's voice; --ref only with Ankush's own recording.

## 2026-11-23 channel rules (Ankush: "ok implement", from vidIQ "How to Escape EVERY YouTube Shorts View Jail", 335K views)
1. Never a plain repost and never mass AI content: every Short adds our own story/title card/captions/edit or narration (reposts and AI slop sit in 0-view jail and get demonetised).
2. One clear channel premise: this channel is ENGLISH GTA 6 streamer moments only. No Hindi uploads here any more (Hindi avg 65 views vs English gags 879); Hindi builds stay banked for a possible separate Hindi channel.
3. Moving gameplay on screen all the time; no static still-image Shorts.
4. Hooks a non-gamer cares about: a mystery, a problem, a payoff promise or nostalgia (GTA 5 vs GTA 6) in the title card and first second.
5. Retention: find the second people leave (averageViewPercentage, retention) and cut it; Shorts just end on the payoff (no spoken "comment/subscribe/thanks" at the end; the question lives in the description). Long videos may ask at the end.
- 23 Nov 20:50 IST: all 4 uploads went through at once when the rolling window opened (5 uploads in 24 h is the real limit). Judge tomorrow: TT-014 curiosity vs 316 median (2x = 630), and LONG-003 (first narrated long video) views + avg % viewed.
- 24 Nov: last night's 32-33 s Speed Shorts (UFO curiosity, gator story) had 2 views each after 9-15 h while 13-17 s gags from mid-size/girl streamers had hundreds by then; the old lowercase pool Short got 2,426 in 19 h. Until the 24 h numbers say otherwise: keep Shorts 12-15 s, avoid the most-reposted streamer (IShowSpeed).
- 24 Nov: 6 uploads in a rolling 24 h went through (4 at 20:50 IST 23 Nov + 2 at 15:07 IST 24 Nov); try uploads early in the run and queue only if refused.
- 26 Nov: first "Guides + secrets" Short TT-020 (UFO how-to, narrated, 32.5 s) went out at 00:15 IST while the channel was stalled. If it beats the post-stall clip Shorts (0-14 views) at 24 h, guides are the way out of the repost competition.
- 26 Nov 00:14: hold still on (+0 views in 9 min, +12 in 17 h). Banked 2 more guides (jet ski dog, Bigfoot). Jet ski dog Shorts by other pages hit 1.3-1.55M in 2-4 days, so secret how-tos have real demand; our blocker is distribution, not the topic.
- Game-only 1080p footage works in a 9:16 crop if the crop pans per scene (ffmpeg crop x as a function of t) - keeps both the player and the subject in frame.
- 27 Nov: UFO guide (TT-020) got 1 view in 26 h, so even a narrated, original guide is not shown - the channel itself is held back, not one format. Ankush's new reference: clean split-screen "If you did X / If you didn't X" reels (no facecam, yellow labels) - try as format I when we have 2 clips of one choice.
- 27 Nov: channel views went DOWN 39 (10,047 -> 10,008) and the Shorts feed has sent ~0 views since 24 Nov (it was 94% of traffic). 5 checks without recovery; guides and clips both get 0-16 views, so the block is channel-level (Studio check needed), not the format.
- 27 Nov: secret-location how-tos are the biggest live lane (gold guns 2.1M, hidden secrets 2.1M) and tiny easter-egg finds win at 8-15 s; Twitch clips almost never name the secret in the title, so guide footage must be searched in streamer Clips tabs, not the category page.
- 28 Nov: the stall broke with guides - Bigfoot guide 1,135 and jet ski dog guide 955 views within hours, while clip Shorts sat at 0-16. Narrated how-to guides are the format; keep them 16-28 s.
- 28 Nov: guides keep working after the stall (Bigfoot 1,135 in ~9 h). Car secrets with keypad codes / hidden garages have many YouTube guides but none with a streamer reaction - our angle. Search words people use (Bugatti, Porsche) go in the title, the in-game names in the description.
- 28 Nov: streamer clips often show burned game subtitles with swears and button prompts; scan the crop at 2-4 fps before choosing keep ranges, and crop the subtitle band off (495x880 from 1080p is still sharp).
