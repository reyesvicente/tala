# Tala — audio to text, no signup

Free audio/video → text transcription. No signup needed, no credit card. Built for Paolo for the
DEV Hacktoberfest Weekend Challenge ("Build for a Friend").

- **Open-weight model:** OpenAI Whisper via [faster-whisper](https://github.com/SYSTRAN/faster-whisper)
  (CTranslate2, int8 on CPU). No third-party AI API is called.
- **Privacy:** audio is deleted the moment it's transcribed; transcripts self-destruct after
  `RETENTION_HOURS` (default 72). Access is by unguessable link only.
- Upload a file or record in the browser · auto-detect ~100 languages · translate to English ·
  export TXT / SRT / WebVTT.

---

## Using Tala

### 1. Add your audio

On the home page, pick one:

- **Upload a file:** drag it onto the box, or click to browse. Most audio and video formats work:
  `mp3`, `m4a`, `aac`, `wav`, `flac`, `ogg`, `webm`, `mp4`, `mov`, and more. Max 100 MB.
- **Record now:** click **Start recording**, allow microphone access, and click **Stop recording**
  when you're done. Use the player that appears to listen before you send it.

### 2. Choose the options

- **Spoken language:** leave it on **Auto-detect**, or pick the language yourself. Picking it
  helps with short clips and mixed-language audio like Taglish.
- **Output:**
  - **Transcript in the same language:** writes down what was said, as it was said.
  - **Translate to English:** gives you English text, whatever language was spoken.

Click **Turn it into text**.

### 3. Wait for it

You're taken to your transcript's private link straight away. The page shows:

- **In line:** another file is being transcribed first. Tala works on one at a time.
- **Preparing audio:** decoding the file and finding the parts with speech. This takes about a
  minute for long recordings.
- **Listening…:** a progress bar with an estimate of the time left.

You don't need to keep the tab open. **Bookmark or copy the link** and come back later.

How long it takes depends on the length of the audio and the server. As a rough guide, a 70-minute
recording took about 13 minutes on a 4-core laptop. Short voice memos take seconds.

### 4. Use the transcript

- **Copy text:** copies the full transcript to your clipboard.
- **Text / SRT subtitles / WebVTT:** downloads the transcript. SRT and VTT include timestamps, so
  you can drop them into a video editor or player as captions.
- **Timestamps:** switch this on to see when each line was said.
- **Delete now:** removes the transcript right away. The link stops working for everyone.

### Your transcripts and privacy

- **Anyone with the link can read the transcript**, so share it only with people you'd show it to.
  This is true whether or not you're logged in.
- Without an account, the home page lists the transcripts **made in this browser** under *Made in
  this browser*. Clearing your browser data, or switching to another device, loses that list, but
  the links still work until they expire.
- The **audio is deleted as soon as it's transcribed**. The text deletes itself after
  **3 days**. Save anything you want to keep with the download buttons.
- Transcription runs on the Tala server itself. Your audio is never sent to an outside AI service.

### Accounts (optional)

You never need an account to transcribe. Creating one adds **My transcripts**: a list of everything
you transcribed while logged in, on any device, with search.

- **Sign up:** click **Sign up** at the top, enter your email and a password (8+ characters).
- **Log in / Log out:** use the buttons at the top right. Logging out ends the session on the server.
- **Forgot password:** on the log-in page, click **Forgot password?** and enter your email. If it has
  an account, you'll get a link that works once, for 60 minutes. Setting a new password logs you out
  on every other device.
- Transcripts in your history still delete themselves after 3 days, like everyone else's.
- **Too many attempts:** after 5 wrong passwords, that account's log-in is paused for 15 minutes.
  Sign-ups and reset requests are also limited per network. The message tells you how long to wait.

### Tips for better results

- Clear audio beats everything: record close to the speaker and avoid background music.
- For non-English audio, set the language yourself instead of using auto-detect.
- Long silences are skipped automatically, so you don't need to trim them.
- The default `base` model is fast but makes mistakes, especially with Tagalog/Taglish. If accuracy
  matters more than speed, ask whoever runs the server to switch to a larger model (see
  [Configuration](#configuration)).

### Troubleshooting

| Problem | What to do |
|---|---|
| "That doesn't look like an audio or video file." | The file isn't media, or its type couldn't be detected. Convert it to mp3 or m4a and try again. |
| "File is larger than 100 MB." | Split the recording, or export it at a lower bitrate (audio-only mp3/m4a is much smaller than video). |
| "Microphone access was blocked." | Allow the microphone in your browser's site settings (padlock icon in the address bar), then reload. |
| Recording isn't available | Your browser doesn't support in-browser recording. Record with your phone's voice memo app and upload the file. |
| "Transcript not found." | It expired after 3 days or was deleted. Upload the audio again. |
| "That one didn't work" | The file couldn't be decoded. It may be damaged or use an unusual codec; convert it to mp3 and retry. |
| Repeated or garbled lines | Whisper sometimes loops on unclear audio. Tala removes most repeats; for better accuracy use a larger model. |

---

## Running it yourself

### Stack

| | |
|---|---|
| API | FastAPI, SQLAlchemy 2, Alembic, PostgreSQL |
| Transcription | faster-whisper (batched decoding), single in-process worker thread (jobs resume after restart) |
| Frontend | React 18 + Vite + TypeScript, TanStack Query, Zustand, React Hook Form + Zod, ice-ds, Tailwind |

### Local development

Requirements: Docker with Compose, and Node.js 20+.

```bash
cp .envs/.local/.api.example .envs/.local/.api
cp .envs/.local/.postgres.example .envs/.local/.postgres

docker compose -f docker-compose.local.yml up --build   # API on :8000, runs migrations on start
cd frontend && npm install && npm run dev                # http://localhost:5173 (proxies /api)
```

The first transcription downloads the Whisper model (~150 MB for `base`) into a Docker volume.

### Backend commands

```bash
docker compose -f docker-compose.local.yml run --rm api pytest
docker compose -f docker-compose.local.yml run --rm api ruff check .
docker compose -f docker-compose.local.yml run --rm api alembic revision --autogenerate -m "..."
```

### Configuration

Set these in `.envs/.local/.api` locally, or as environment variables in production.

| Variable | Default | |
|---|---|---|
| `DATABASE_URL` | local Postgres | SQLAlchemy URL, e.g. `postgresql+psycopg://user:pass@host:5432/db` |
| `WHISPER_MODEL` | `base` | `tiny`, `base`, `small`, `medium`, `large-v3`, `large-v3-turbo`. Bigger is more accurate, slower, and needs more RAM. |
| `WHISPER_COMPUTE_TYPE` | `int8` | Quantization; `int8` is best on CPU |
| `WHISPER_BATCH_SIZE` | `8` | Speech chunks decoded in parallel |
| `WHISPER_BEAM_SIZE` | `1` | `1` = greedy (fastest); `5` is slower |
| `WHISPER_REPETITION_PENALTY` | `1.1` | Discourages repetition loops |
| `WHISPER_NO_REPEAT_NGRAM_SIZE` | `0` | Set to e.g. `4` to block loops harder (may also clip real repeats) |
| `MAX_UPLOAD_MB` | `100` | Upload size limit |
| `RETENTION_HOURS` | `72` | How long transcripts live |
| `APP_URL` | `http://localhost:5173` | Public URL of the site, used in password-reset links |
| `RESEND_API_KEY` | unset | [Resend](https://resend.com) key for reset emails. Unset: links are printed in the API logs |
| `EMAIL_FROM` | `Tala <noreply@rs.vicentereyes.org>` | Sender; its domain (`rs.vicentereyes.org`) must be verified in Resend |
| `COOKIE_SECURE` | `true` | Set `false` for plain-http local dev |
| `SESSION_DAYS` | `30` | How long a login lasts |

### API

All JSON responses use `{ "data": ..., "message": "", "errors": null }`.

| Method | Path | |
|---|---|---|
| `GET` | `/api/info` | model, limits, language list |
| `POST` | `/api/transcriptions` | multipart: `file`, optional `language`, `task` (`transcribe`/`translate`) → 202 |
| `GET` | `/api/transcriptions/{slug}` | status, progress, text, segments |
| `GET` | `/api/transcriptions/{slug}/export/{txt,srt,vtt}` | download |
| `DELETE` | `/api/transcriptions/{slug}` | delete now |
| `GET` | `/api/transcriptions?page=&page_size=&q=` | logged-in user's history (paginated, search by file name) |
| `POST` | `/api/auth/register` | `{email, password}` → creates account, logs in |
| `POST` | `/api/auth/login` | `{email, password}` → sets session cookie |
| `POST` | `/api/auth/logout` | ends the session |
| `GET` | `/api/auth/me` | current user, or 401 |
| `POST` | `/api/auth/forgot-password` | `{email}` → always 202; emails a reset link if the account exists |
| `POST` | `/api/auth/reset-password` | `{token, password}` → sets new password, logs out other sessions |

Sessions are server-side: the browser holds an `httpOnly`, `SameSite=Lax` cookie and the database
stores only a SHA-256 of it. Passwords are hashed with Argon2.

Rate limits (in memory, per instance): login 20 per IP / 5 min and 5 failures per email / 15 min;
register 5 per IP / hour; forgot-password 5 per IP / 15 min; reset-password 10 per IP / 15 min.
Blocked requests return `429` with a `Retry-After` header.

OpenAPI docs: http://localhost:8000/api/docs

Example with `curl`:

```bash
curl -F file=@memo.m4a -F language=tl http://localhost:8000/api/transcriptions
curl http://localhost:8000/api/transcriptions/<slug>
curl -OJ http://localhost:8000/api/transcriptions/<slug>/export/srt
```

### Production

`compose/production/Dockerfile` builds a single image that serves the frontend and the API from one
origin. The Whisper model is downloaded at build time, so the container never calls the Hugging Face
Hub at runtime. Choose the model with a build argument:
`docker build --build-arg WHISPER_MODEL=small -f compose/production/Dockerfile .`

It needs `DATABASE_URL`, honors `PORT`, and runs migrations on start. Deployment notes:

- Give it at least 2 GB RAM for `base`, and 4 GB with 2+ CPUs for `small` or `large-v3-turbo`.
- Run **one** instance only; the job queue lives inside the process.
- Optionally mount a persistent disk at `/data` so jobs in progress survive a redeploy.

### Deploy to Render

`render.yaml` is a Render Blueprint: one web service (frontend + API in one image) and a Postgres
database, in the Singapore region.

1. Push this repo to GitHub.
2. In the [Render Dashboard](https://dashboard.render.com), choose **New → Blueprint** and pick the
   repo. Render reads `render.yaml` and shows the web service and database it will create.
3. Click **Apply**. The first build takes several minutes because it installs the dependencies and
   downloads the Whisper model into the image.
4. Open the `.onrender.com` URL shown on the `tala` service. Migrations run automatically on start.

Plans in the blueprint:

| Resource | Plan | Why |
|---|---|---|
| Web service | `1c-2g` (1 CPU, 2 GB) | Whisper `base` uses ~500 MB while transcribing, so the 512 MB plans are too small. With 1 CPU, expect long files to take longer than on a laptop. |
| Disk | 1 GB at `/data` | Keeps uploads that are waiting to be transcribed across deploys and restarts. |
| Postgres | `free` | Enough for a demo. Render's free databases have limits and can expire; move to a paid plan (e.g. `0.1c-256mb`) to keep it long-term. |

Check Render's pricing page for current costs, and apply any credits you have before deploying.
To change the model, edit `ARG WHISPER_MODEL` in `compose/production/Dockerfile` (the model is
baked into the image), and pick a bigger plan for `small` or larger.
