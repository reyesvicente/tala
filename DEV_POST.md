---
title: "Tala: Free Audio-to-Text for My Designer Friend (No Signup, No Credit Card)"
published: false
tags: devchallenge, weekendchallenge, hf26challenge, ai
---

*This is a submission for the [Hacktoberfest Weekend Challenge: Build for a Friend](https://dev.to/challenges/hacktoberfest-weekend-2026-10-01)*

## What I Built

Paolo, a designer I work with, asked me a simple question:

> "Do you know an app that turns audio into text that doesn't make me sign up or put in a credit card?"

I couldn't name one. Every tool I knew wanted an account, a "free trial" that asked for a card up front, or had a monthly minutes cap. Paolo just wanted to drop in a recording of a client call or a voice memo and get the words back.

So I built **Tala** (Tagalog for *note* or *record*). It does one thing:

**Audio in. Text out. No signup, no card, no catch.**

- **Upload or record:** drag in a voice memo, meeting, or interview (mp3, m4a, aac, wav, ogg, webm, even mp4 video), or record in the browser and play it back before sending.
- **~100 languages:** auto-detected, including Tagalog/Filipino, which matters for us. There's also a one-click **translate to English** option.
- **Exports:** copy the text, or download plain text, **SRT**, or **WebVTT**. Paolo can drop the subtitle files straight into video edits.
- **Timestamps toggle:** see when each line was said.
- **A private link instead of a signup:** every transcript gets a hard-to-guess URL, and your browser remembers the ones you made.
- **Optional accounts:** if you want your transcripts on every device, sign up with an email and password to get a searchable **My transcripts** history. It's never required to transcribe. Forgot-password emails a one-time reset link.
- **Self-destructing data:** the audio is deleted the moment it's transcribed. The text deletes itself after 72 hours, or right away with **Delete now**.

<!-- Bonus points: hand it to Paolo and add what he said here. -->

## Demo

🌐 **Try it live: [tala.vicentereyes.org](https://tala.vicentereyes.org)**. No signup, just drop in a file.

▶️ **[Watch the demo video](https://share.vidyard.com/watch/qtnjGHRDCkx56fe2cLSBjx)**

The flow is three screens:

1. **Home:** drop a file or hit *Record now*, pick a language (or leave it on auto-detect), and click **Turn it into text**.
2. **Progress:** you land on your private link right away. It shows *Preparing audio*, then a live progress bar with an estimate of the time left. You can close the tab and come back.
3. **Transcript:** copy, download TXT/SRT/VTT, toggle timestamps, or delete it.

## Code

The full source is on GitHub: **[github.com/reyesvicente/tala](https://github.com/reyesvicente/tala)**. Run it locally with Docker and npm by following the README.

{% github reyesvicente/tala %}

## How I Built It

### The open-source AI at the core: Whisper

The model is OpenAI's **Whisper**, an open-weight speech recognition model, run through **[faster-whisper](https://github.com/SYSTRAN/faster-whisper)**. faster-whisper reimplements Whisper on CTranslate2, so it runs on a plain CPU with **int8** quantization. No GPU and no external API.

```
React (Vite) ──/api──▶ FastAPI ──▶ PostgreSQL
                         │
                         └─▶ worker thread ──▶ faster-whisper (local CPU)
```

**Backend: FastAPI + SQLAlchemy 2 + Alembic + PostgreSQL**

- `POST /api/transcriptions` streams the upload to disk in 1 MB chunks, enforcing the size limit without holding the file in memory. It saves a `pending` row and immediately returns **202** with the slug.
- One **in-process worker thread** runs Whisper on one file at a time, so a CPU-heavy model doesn't overload the machine. On startup, unfinished jobs go back into the queue, so a restart doesn't lose anyone's work.
- The audio file is deleted in the same step that saves the transcript, and also when a job fails. A periodic purge removes expired transcripts.
- **Optional accounts** use server-side sessions: the browser holds an `httpOnly` cookie, the database stores only a SHA-256 of it, and passwords are hashed with Argon2. Logging out ends the session on the server, and resetting a password logs out every device. Forgot-password answers the same way whether or not the email exists, and reset links arrive through [Resend](https://resend.com).
- **Rate limits** on login, sign-up and password resets: 5 failed logins lock that email for 15 minutes, and blocked requests get a `429` with `Retry-After`.
- The tests swap Whisper for a fake transcriber, so all 35 tests, from uploads to the full password-reset flow, run in seconds.

**Frontend: React 18 + Vite + TypeScript**

- **TanStack Query** polls the transcript every 1.5 seconds *only* while it's `pending` or `processing`, then stops.
- **Zustand** (persisted) stores the "made in this browser" list, so people who never sign up still keep track of their transcripts.
- **MediaRecorder** handles in-browser recording, picking whatever codec the browser supports. The backend decodes all of them through PyAV.
- The UI is built with [ice-ds](https://www.npmjs.com/package/ice-ds), my neubrutalist component library.

**Deployment: [Render](https://render.com).** One Docker image builds the React app, installs the API, and bakes the Whisper model in at build time. FastAPI serves the frontend and the API from one origin, and the container never contacts the model hub at runtime. A `render.yaml` Blueprint defines the whole stack: a Docker web service running Whisper on CPU (1 CPU, 2 GB) plus Render Postgres, both in Singapore, close to Paolo. Every push to `main` redeploys automatically, and the live site is at [tala.vicentereyes.org](https://tala.vicentereyes.org).

### What testing on a real recording taught me

My first test was an 11-second clip, and it worked well. Then I tried a real **70-minute Tagalog meeting recording**, and two things broke.

**1. It was far too slow.** The progress bar barely moved. I benchmarked a 3-minute slice of the recording on my 4-core laptop:

| Settings | Speed |
|---|---|
| Sequential decoding, beam 5 (my original settings) | 0.6× real time |
| Sequential decoding, beam 1 | 0.7× real time |
| **Batched decoding (`BatchedInferencePipeline`), batch 8, beam 1** | **3.8× real time** |

Batched decoding first uses voice-activity detection to cut the audio into speech chunks, then decodes several chunks at once. Switching to it took the full 70-minute file from **about 2 hours to 13 minutes**. I also added a *Preparing audio* stage and a time-left estimate, so a long job no longer looks frozen.

**2. Whisper hallucinated.** On hard audio, small Whisper models get stuck in loops, and the transcript filled up with lines like `ngayon ngayon ngayon …` and `kakakakaka…`. One unbroken loop was so long it pushed the page wider than the screen. Batched mode decodes at a single temperature, so Whisper's usual retry-on-repetition fallback never runs. I added:

- a decoder `repetition_penalty`
- a small cleanup step that collapses repeated phrases and in-word loops (`sa-ma-ma-ma-ma` → `sa-ma`), drops segments that are just `...`, and merges duplicate lines
- CSS so long strings wrap instead of overflowing

On that meeting, the cleanup cut the transcript from 5,458 words to 1,425. That tells you how much of it was noise.

**The honest result:** the cleanup removes junk, but the default `base` model still struggles with Taglish conversation. Because the model is open, fixing that is a config change rather than a vendor negotiation: `WHISPER_MODEL=small` or `large-v3-turbo` trades speed for accuracy.

**One more bug:** the first real transcription failed with `open() got an unexpected keyword argument 'metadata_errors'`. faster-whisper 1.2.1 passes an argument that PyAV 19 removed. Pinning `av==15.1.0` fixed it, and the failure path worked as designed: the job was marked `failed`, the user saw a clear message, and the audio was still deleted.

## Why Does Open Innovation Matter?

The whole idea of Tala, *no signup and no credit card*, only works because the model is open.

**It costs nothing per minute.** Hosted speech-to-text APIs bill per minute of audio. A free product built on one needs an account to rate-limit you, or a card to bill you, which is exactly the friction Paolo wanted to avoid. With Whisper running on my own server, the cost is the server, so a free tool with no strings attached actually works.

**The audio never leaves a machine I control.** Paolo's recordings are client calls and design reviews. With a closed API, every file goes to a third party under their retention policy. With Tala, the audio is decoded on the server it was uploaded to and deleted minutes later. I can promise that because I can read every line of code it passes through.

**I could open it up and fix it.** When Tala was too slow on long files, I didn't wait for a provider to ship a faster tier. I benchmarked decoding strategies on my own laptop and switched to batched inference: 6× faster in an afternoon. When it hallucinated on Tagalog, I could see exactly why (no temperature fallback in batched mode) and add guards. A closed API is a black box: you get what it returns.

**I can swap models freely.** `tiny` for a cheap host, `large-v3-turbo` for accuracy. It's one environment variable, with no lock-in and no deprecation emails. If Tagalog accuracy is still not good enough, the weights are open, so fine-tuning is an option.

**It runs on a laptop.** The local dev setup is the full product. No API keys, and no internet after the model downloads once. Anyone can clone the repo and run their own private transcriber.

Where closed is better: hosted APIs run on GPUs, so long files finish faster, and they offer speaker labels. On a modest CPU, an hour of audio takes a while. For Paolo's usual 5–15 minute memos and calls, that trade-off is fine.

## My Agent Session

<!-- Optional: save this session with DevRelay and embed it with the agent_session tag, or link to it. -->

I built Tala pair-programming with Claude Code: scaffolding, the benchmark that found the batched-decoding speedup, and debugging the hallucination loops all happened in that session.

## Prize Categories

- **Best Use of Render:** Render is Tala's AI runtime. The open-weight Whisper model runs inside a Render web service, with Render Postgres for jobs and transcripts, all defined in a one-file Blueprint.

Thanks for reading, and if you need audio turned into text, no signup required. 🎧
