# AI Channel Video Pipeline

topic -> script (Claude) -> voiceover (edge-tts, free) -> visuals (Pexels or gradient cards) -> captions + render (ffmpeg) -> YouTube upload

## Setup
    pip install edge-tts anthropic google-api-python-client google-auth-oauthlib pillow requests
    # ffmpeg must be installed
    export ANTHROPIC_API_KEY=...
    export PEXELS_API_KEY=...      # optional, free at pexels.com/api (otherwise gradient cards are used)
    # optional: put royalty-free background music at ./music.mp3

## YouTube upload (one time)
1. console.cloud.google.com -> new project -> enable "YouTube Data API v3"
2. Credentials -> OAuth client ID -> Desktop app -> download as `client_secret.json` into this folder
3. OAuth consent screen: add your Google account as a test user
4. First `--upload` opens a browser to log in; saves token.json
Note: videos from unverified API projects are locked to private until the project passes Google's audit. Request it at https://support.google.com/youtube/contact/yt_api_form

## Run
    python main.py "How AI agents work" --review     # make script, edit out/<slug>/script.json
    python main.py --from-script out/<slug>/script.json --upload
    python main.py "Topic" --upload --publish-at 2026-11-02T12:00:00Z

## Phone-only (GitHub Actions)
1. Create a repo, upload this whole folder (including the hidden `.github` folder).
2. Repo -> Settings -> Secrets and variables -> Actions, add: `PEXELS_API_KEY` (optional), and for upload
   `YT_CLIENT_ID`, `YT_CLIENT_SECRET`, `YT_REFRESH_TOKEN`.
   Refresh token: Google Cloud OAuth client (type Web) with redirect https://developers.google.com/oauthplayground,
   then at developers.google.com/oauthplayground use your own credentials (gear icon), scope
   https://www.googleapis.com/auth/youtube.upload, authorize, exchange code, copy the Refresh token.
3. Actions tab -> "Make video" -> Run workflow -> choose script, tick upload. Video is also downloadable from the run's Artifacts.
Add new videos by adding scripts/videoNN.json files (same format as video01.json).
