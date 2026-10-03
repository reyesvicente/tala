---
title: "Tala: Free Audio-to-Text for My Designer Friend (No Signup, No Credit Card)"
published: false
tags: devchallenge, weekendchallenge, hf26challenge, ai
---

*This is a submission for the [Hacktoberfest Weekend Challenge: Build for a Friend](https://dev.to/challenges/hacktoberfest-2026)*

## What I Built

Paolo, a designer I work with, asked me a simple question:

> "Do you know an app that turns audio into text that doesn't make me sign up or put in a credit card?"

I couldn't name one. Every tool I knew wanted an account, a "free trial" that asked for a card up front, or a monthly minutes cap. Paolo only wanted to drop in a recording of a client call or a voice memo and get the words back.

So I built **Tala** (Tagalog for *note* or *record*). It does one thing:

**Audio in. Text out. No account, no card, no catch.**

- **Upload or record:** drag in a voice memo, interview, or meeting recording (mp3, m4a, wav, ogg, webm, even mp4 video), or record straight from the browser and play it back before sending.
- **~100 languages:** the language is detected automatically, including Tagalog/Filipino, which matters for us. There's also a one-click **translate to English** option.
- **Exports:** copy the text, or download it as plain text, **SRT**, or **WebVTT** subtitles. Paolo can drop the subtitle files straight into video edits.
- **Timestamps toggle:** see where each line was said.
- **A private link instead of an account:** every transcript gets a short, hard-to-guess URL. Your browser remembers the ones you made, and that's the whole "account system."
- **Self-destructing data:** the audio is deleted the moment it's transcribed. The text deletes itself after 72 hours, or right away when you click **Delete now**.

## Demo

<!-- Add a screenshot or short screen recording of: upload → progress bar → transcript -->

**Code:** <!-- link to your GitHub repo -->

The flow is three screens:

1. **Home:** drop a file or hit *Record now*, pick a language (or leave it on auto-detect), and click **Turn it into text**.
2. **Progress:** you land on your private link right away, and a progress bar fills as Whisper works through the audio. You can bookmark it and come back.
3. **Transcript:** copy, download TXT/SRT/VTT, toggle timestamps, or delete it.

## How I Built It

### The open-source AI at the core: Whisper

The model is OpenAI's **Whisper**, an open-weight speech recognition model, run through **[faster-whisper](https://github.com/SYSTRAN/faster-whisper)**. faster-whisper reimplements Whisper on CTranslate2, so it runs well on a plain CPU with **int8** quantization. No GPU needed.

On my 4-core laptop, the `base` model took about 10–15 seconds from clicking the button to seeing the transcript of an 11-second clip. Switching to a bigger, more accurate model is one environment variable:

```bash
WHISPER_MODEL=small   # tiny | base | small | medium | large-v3
```

Two faster-whisper features did a lot of the work:

- **`vad_filter=True`:** voice-activity detection skips silence before decoding. Long recordings with pauses run faster, and Whisper is less likely to "hallucinate" text in the quiet parts.
- **Segments come from a generator.** Decoding happens as you iterate, so I can write progress to the database as each segment finishes. That's what drives the live progress bar in the UI.

```python
segments_iter, info = model.transcribe(
    audio_path, language=language, task=task, vad_filter=True, beam_size=5
)
for seg in segments_iter:  # decoding happens as we iterate
    segments.append({"start": seg.start, "end": seg.end, "text": seg.text.strip()})
    on_progress(min(seg.end / info.duration, 0.99))
```

`task="translate"` is built into Whisper, so the "translate to English" feature cost me one dropdown.

### Architecture

```
React (Vite) ──/api──▶ FastAPI ──▶ PostgreSQL
                         │
                         └─▶ worker thread ──▶ faster-whisper (local CPU)
```

**Backend: FastAPI + SQLAlchemy 2 + Alembic + PostgreSQL**

- `POST /api/transcriptions` streams the upload to disk in 1 MB chunks, enforcing the size limit without buffering the whole file in memory. It then saves a `pending` row and returns **202** with the slug right away.
- One **in-process worker thread** takes jobs from a queue and runs Whisper one file at a time, so a CPU-bound model doesn't oversubscribe the machine. On startup, rows still marked `pending` or `processing` go back into the queue, so a container restart doesn't lose anyone's job.
- When a job finishes, the audio file is deleted in the same step that saves the transcript. Failed jobs also delete their audio.
- A periodic purge removes transcripts past their `expires_at`, plus any orphaned uploads.
- Every response uses the same envelope: `{ "data": ..., "message": "", "errors": null }`.
- Routers stay thin and business logic lives in `services/`. Tests swap the real model for a fake transcriber and run jobs synchronously, so they finish in under half a second.

**Frontend: React 18 + Vite + TypeScript**

- **TanStack Query** handles all server state. The transcript query polls every 1.5 seconds *only* while the status is `pending` or `processing`, then stops:

  ```ts
  refetchInterval: (query) => {
    const status = query.state.data?.status;
    return status === "pending" || status === "processing" ? 1500 : false;
  },
  ```

- **Zustand** (with `persist`) stores the "made in this browser" list. That list is how Tala gets away with having no accounts.
- **React Hook Form + Zod** handle the upload form.
- **MediaRecorder** handles in-browser recording. It picks whichever codec the browser supports (webm/opus on Chrome and Firefox, mp4 on Safari), and the backend decodes all of them through PyAV.
- **[ice-ds](https://www.npmjs.com/package/ice-ds)**, my neubrutalist component library, provides the UI: hard borders, offset shadows, and loud colors.

**Deployment:** one production Dockerfile builds the React app, installs the API, and **downloads the Whisper model into the image** at build time, so cold starts don't download 150 MB. FastAPI serves the SPA and the API from the same origin.

### The bug that almost cost me an evening

The first real transcription failed with:

```
open() got an unexpected keyword argument 'metadata_errors'
```

faster-whisper 1.2.1 passes `metadata_errors=` to `av.open()`, and the latest PyAV (19.x) removed that argument. Pinning `av==15.1.0` fixed it. The useful part: my error handling worked as designed. The job was marked `failed`, the user saw a clear message, and the audio was still deleted.

## Why Open Innovation Matters Here

The whole idea of Tala, *no signup and no credit card*, only works because the model is open.

**It costs nothing per minute to run.** Hosted speech-to-text APIs charge per minute of audio. A free service built on one either needs an account to rate-limit you, or a card on file to bill you. That's exactly the friction Paolo wanted to avoid. With Whisper running on my own box, the cost is a server I already pay for, so a free tier with no strings attached actually works.

**The audio never leaves a machine I control.** Paolo's recordings are client calls and design reviews. With a closed API, every file goes to a third party under their retention policy. With Tala, the audio is decoded on the same server it was uploaded to and deleted seconds later. I can promise that because I can read every line of code it passes through.

**I can swap and tune the model freely.** `tiny` for a cheap host, `large-v3` for accuracy, `distil-large-v3` for a middle ground. It's one environment variable, with no vendor lock-in and no deprecation emails. If Tagalog accuracy isn't good enough, the weights are open, so fine-tuning is an option.

**It runs on a laptop.** The local dev setup is the full product. No API keys, no internet needed after the model downloads once. Anyone can clone the repo and run their own private transcriber.

Where closed was better: hosted APIs are faster on long files because they run on GPUs, and they come with speaker labels. On a CPU, a one-hour meeting takes a while. For Paolo's typical 5–15 minute memos and calls, that trade-off is fine.

## What Paolo Said

<!-- Hand it over to Paolo and write his actual reaction here. -->

## What's Next

- Speaker labels ("who said what") for meeting recordings
- An optional summary or clean-up pass with an open LLM like Gemma, running locally as well
- A public deployment so Paolo doesn't need my laptop running

Thanks for reading, and if you need audio turned into text, no signup required. 🎧
