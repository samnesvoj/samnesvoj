# Project notes

Detailed technical notes behind the cards on my profile.

## SONYA — [sonya.group](https://sonya.group/) (private repository)

An AI video platform. You submit a long video or a link, and it returns 1080×1920 clips cut for short-form feeds.

- **Pipeline:** FastAPI API → PostgreSQL job queue → systemd dispatcher → ephemeral vast.ai GPU instance
  running a Docker worker image from GHCR → results stored in S3 and served by presigned URLs.
- **Modes:** `trailer` · `virality` · `stories` · `educational` in production, plus `streamer` in beta. Each mode is a
  self-contained runner with a `mode.yaml` that declares its models, which are pulled from S3 before a job runs.
- **Vision & audio:** YOLO11 detection and pose plus custom weights, MediaPipe active-speaker detection, faster-whisper
  transcription, PySceneDetect, Gemini layout analysis, FFmpeg rendering.
- **Security:** passwordless email codes stored as HMAC hashes, HttpOnly session cookies, constant-time worker auth,
  rate limiting, magic-byte upload validation, strict CORS.
- **Reliability:** idempotent job submission, a cap on concurrent GPU jobs, startup SLA timeouts and a bad-host
  blacklist for vast.ai, and durable instance cleanup.
- **Quality:** 150+ pytest tests, PostgreSQL integration tests in CI, Node frontend tests, and worker images built by
  GitHub Actions.
- **Frontend:** a vanilla JS web app and a Telegram Mini App, with a Three.js / WebGL cloth-simulation hero.

## SONYA GROUP Bot — [repository](https://github.com/samnesvoj/sonya-group-bot)

The Telegram entry point to SONYA.

- **Consent-gated onboarding:** three versioned legal documents. Bumping a version re-prompts users, and every
  acceptance is recorded in an SQLite audit trail.
- **Main menu:** opens the SONYA Mini App and has account info, help/FAQ and a payment screen.
- **Retention messaging:** runs on APScheduler, and sends stay idempotent through an atomic SQLite claim.
- **Engineering:** aiogram 3 routers and middlewares, schema migrations, rotating logs, a systemd unit, 83 pytest tests.

## PyLens — [repository](https://github.com/samnesvoj/PyLens) · [live demo](https://py-lens.vercel.app)

An interactive web app for learning Python functions and methods visually.

- 31 functions and methods, each with an example and a visualization.
- A random example generator and a 10-question quiz trainer.
- Search, category filters and favorites saved in `localStorage`.
- Next.js 15 App Router, React 19, TypeScript, Tailwind CSS, Framer Motion.

## Content automation (private repositories)

- **Yandex Zen articles:** an n8n schedule picks a niche and topic, then one of two writing personas produces the
  article through an LLM (Grok via OpenRouter). A Telegram approval bot on Vercel serverless functions and Supabase
  gates publishing through an RSS endpoint.
- **TikTok pipeline:** Apify scraping → a Supabase status machine (`pending → approved → ready → published`) → n8n +
  OpenRouter for captions and hashtags → Klap AI clipping → Telegram moderation (TypeScript, Telegraf) → publishing
  through the Upload-post API.

## Google Forms & Apps Script

Custom Google Forms built programmatically with Google Apps Script: generated form structure, response handling,
automatic writes to Google Sheets, notifications and integrations with other services through Google APIs.

## More builds

| Project | What it is | Stack |
|---|---|---|
| Aminelli (private) | Mobile-first storefront for a flower shop: catalog, cart, stores and warehouses, plus an accounting-service layer for 1C with mock and real adapters | React · TypeScript · Vite · Tailwind · Radix UI |
| SONYA Mini App (private) | Telegram Mini App front end for video generation, with a page per mode and theming | Vanilla JS · HTML · CSS · Telegram WebApp |
| SONYA GPU bench (private) | Standalone benchmark kit for testing the video modes on rented GPUs | Python · YOLO · faster-whisper |
| [CryptoGuard](https://github.com/samnesvoj/cpp-middle-project-sprint-1) | C++ file encryption CLI on OpenSSL EVP (in progress) | C++23 · CMake · Conan · Boost · GoogleTest |
