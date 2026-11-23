import type { Register } from 'claude-code'

// Shared context every command starts from, so a brand-new chat knows the channel.
const BASE = [
  'Channel: Theft Talk (@thefttalk), a GTA 6 YouTube Shorts channel, channel ID UCgppTvPhWdNG-scO-fQPyfA.',
  'Follow the theft-talk-studio skill if it is installed, and use my Zapier skills theft-talk-upload-short, theft-talk-channel-stats and theft-talk-reschedule (read them with get_zapier_skill).',
  'Tools and tracking live in GitHub repo ankush2001/New-Project, branch thefttalk-tools (tracking/log.md, scoreboard.csv, learning.md, bank.md, missions.md); render on my Mac in ~/faceless-shorts/tt-tools.',
  'Rules: every upload is private with a publish time (never instantly public); pick the format from what is trending and what fits the clip (story Short with white title card + word-by-word captions, quick gag with top banner + punch-in, curiosity, series, countdown, Hindi guide); credit the streamer on screen and in line 1 of the description; no story spoilers, leaks, AI fakes, sexual content or Rockstar logos/art; never reuse a clip from the log.',
].join(' ')

type Cmd = {
  name: string
  description: string
  argumentHint?: string
  ask: (args: string) => string
  note: string
}

const COMMANDS: Cmd[] = [
  {
    name: 'tt-short',
    description: 'Theft Talk: find, cut and schedule one GTA 6 clip Short',
    argumentHint: '[streamer, Twitch clip link or idea]',
    ask: a =>
      `Make one Theft Talk clip Short end to end${a ? ` from this: ${a}` : ''}. ` +
      'If I gave no clip, scout Twitch GTA 6 clips from the last 24 h in the built-in browser (side-mission moments, girl streamers, big streamers, curiosity moments first), pick the most share-worthy payoff, cut it with clip.py (banner + punch-in), look at the QA frames, host it on a media-YYYYMMDD branch and schedule it in the next free slot with theft-talk-upload-short. Log it in tracking and tell me the title, IST time and youtu.be link.',
    note: 'Theft Talk: making one Short…',
  },
  {
    name: 'tt-today',
    description: "Theft Talk: fill the next 24 hours of Shorts (today's batch)",
    ask: () =>
      'Do today\'s Theft Talk batch: run theft-talk-channel-stats with trends, count what is already scheduled in the next 24 h, then fill the free slots (19:30 girl streamer, 21:30 Hindi news or side-mission guide, 23:30 side-mission moment, 05:30 strongest clip; 2 h apart; max 4 uploads). Finish with a short summary: yesterday\'s best and worst Short with views, today\'s titles with IST times and youtu.be links, the bank, anything skipped.',
    note: "Theft Talk: starting today's batch…",
  },
  {
    name: 'tt-upload',
    description: 'Theft Talk: schedule a finished Short on YouTube',
    argumentHint: '[MP4 link or file] [IST time] [streamer + clip link]',
    ask: a =>
      `Schedule this finished Short on @thefttalk with the theft-talk-upload-short Zapier skill: ${a || '(ask me which video and when)'}. ` +
      'If it is a local file or attachment, host it first on a media-YYYYMMDD branch of ankush2001/New-Project and use the raw link. Write the title and description with the channel template, upload private with publish_at, verify publishAt, log it, and give me the youtu.be link and IST time.',
    note: 'Theft Talk: scheduling the upload…',
  },
  {
    name: 'tt-stats',
    description: 'Theft Talk: channel stats, winners and what is trending',
    argumentHint: '[optional: trends]',
    ask: a =>
      `Run the theft-talk-channel-stats Zapier skill${/trend/i.test(a) ? ' including the trends check' : ''} and give me a short report: best and worst Shorts with views and % viewed, momentum winners, what is scheduled (IST), top countries, and one suggestion for today.`,
    note: 'Theft Talk: pulling channel stats…',
  },
  {
    name: 'tt-reschedule',
    description: 'Theft Talk: move, cancel or re-word a Short',
    argumentHint: '[youtu.be link or title] [new IST time | cancel | new title/description]',
    ask: a =>
      `Use the theft-talk-reschedule Zapier skill for this: ${a || '(ask me which video and what to change)'}. Never delete a video; to take one down, set it private. Confirm the result in one or two lines with the link.`,
    note: 'Theft Talk: updating the Short…',
  },
  {
    name: 'tt-guide',
    description: 'Theft Talk: Hindi side-mission guide Short',
    argumentHint: '[side mission name]',
    ask: a =>
      `Make a Hindi side-mission quick guide Short${a ? ` for: ${a}` : ' for the next side mission not yet in tracking/missions.md'}. ` +
      'Facts only from 2 guide sites searched today that agree; 25-35 s; news_stills.py stills (no Devanagari conjuncts on stills) and hi-IN-MadhurNeural edge-tts at +10% on my Mac; title in Devanagari with the English mission name; schedule it at 21:30 IST (or the next free slot) with theft-talk-upload-short and log it in tracking/missions.md.',
    note: 'Theft Talk: making the Hindi guide…',
  },
]

export const register: Register = on => {
  on('session.start', async ($, e, next) => {
    for (const c of COMMANDS) {
      await $.command.register({
        name: c.name,
        description: c.description,
        ...(c.argumentHint ? { argumentHint: c.argumentHint } : {}),
      })
    }

    return next(e)
  })

  for (const c of COMMANDS) {
    on('command.run', { command: c.name }, async ($, e) => {
      const args = e.args.trim()
      // Not awaited: the prompt becomes its own turn once this command has finished.
      void $.prompt
        .submit({ text: `${c.ask(args)}\n\n${BASE}`, asUser: true })
        .catch(() => $.ui.toast(`Theft Talk: could not start /${c.name}. Type the request in the chat instead.`))

      return { text: c.note, isTextDisplayOnly: true }
    })
  }
}
