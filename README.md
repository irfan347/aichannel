# AI Channel Video Pipeline

script JSON -> voice (free Edge TTS, or ElevenLabs) -> animated slides + lip-sync presenter -> captions ->
landscape video + vertical Short + thumbnail -> optional YouTube upload. Runs on GitHub Actions from a phone.

## Make a video (phone)
github.com/irfan347/aichannel/actions (Chrome "Desktop site") -> Make video -> Run workflow.
Download from the run's **Artifacts -> video** (final.mp4, short.mp4, thumbnail.png).

## Secrets (Settings -> Secrets and variables -> Actions), all optional
- `PEXELS_API_KEY` – stock footage for `stock` scenes (free, pexels.com/api)
- `ELEVENLABS_API_KEY` – more natural voice (paid). Optional `ELEVEN_VOICE_ID`.
- `YT_CLIENT_ID`, `YT_CLIENT_SECRET`, `YT_REFRESH_TOKEN` – auto upload (see below)

## Script format (scripts/videoNN.json)
title, description, tags, thumbnail_text, short_title, scenes[]: narration + screen.
screen types: `title` (title, subtitle), `chat` (user, ai), `steps`/`bullets`/`checklist` (title, items),
`stock` (query, title). Add `"presenter": false` to a scene to hide the character.

## YouTube upload refresh token
Google Cloud -> enable YouTube Data API v3 -> OAuth client (Web) with redirect
https://developers.google.com/oauthplayground -> at the OAuth Playground use your own credentials (gear icon),
scope https://www.googleapis.com/auth/youtube.upload, authorize, exchange code, copy Refresh token.
Unaudited API projects upload as private only. Custom thumbnails need a phone-verified channel.
