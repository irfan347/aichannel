"""Step 2: narration -> clean voice WAV + per-word timings.
ElevenLabs if ELEVENLABS_API_KEY is set (with word timestamps), otherwise free Microsoft Edge TTS
(word boundaries). The voice is then cleaned: rumble removed, de-essed, compressed. Loudness is
normalised once on the full track in render.py."""
import asyncio, base64, os, re, subprocess, threading
import requests

EDGE_VOICES = [os.getenv("EDGE_VOICE", "en-US-AndrewMultilingualNeural"), "en-US-AndrewNeural", "en-US-GuyNeural"]
EDGE_RATE = os.getenv("EDGE_RATE", "+2%")
ELEVEN_VOICE = os.getenv("ELEVEN_VOICE_ID", "pNInz6obpgDQGcFmaJgB")  # "Adam" premade voice


def _in_thread(fn):
    """run an asyncio job in its own thread (works even if another event loop is running)"""
    out, err = [], []

    def job():
        try:
            out.append(asyncio.run(fn()))
        except Exception as e:
            err.append(e)
    t = threading.Thread(target=job); t.start(); t.join()
    if err:
        raise err[0]
    return out[0]


def _edge(text, path, voice):
    async def go():
        import edge_tts
        try:
            c = edge_tts.Communicate(text, voice, rate=EDGE_RATE, boundary="WordBoundary")
        except TypeError:  # older edge-tts always sends word boundaries
            c = edge_tts.Communicate(text, voice, rate=EDGE_RATE)
        words = []
        with open(path, "wb") as f:
            async for ch in c.stream():
                if ch["type"] == "audio":
                    f.write(ch["data"])
                elif ch["type"] == "WordBoundary":
                    s = ch["offset"] / 1e7
                    words.append([s, s + ch["duration"] / 1e7, ch["text"]])
        return words
    return _in_thread(go)


def _eleven(text, path):
    r = requests.post(f"https://api.elevenlabs.io/v1/text-to-speech/{ELEVEN_VOICE}/with-timestamps",
                      headers={"xi-api-key": os.environ["ELEVENLABS_API_KEY"]},
                      json={"text": text, "model_id": "eleven_multilingual_v2",
                            "voice_settings": {"stability": 0.45, "similarity_boost": 0.8, "style": 0.25}},
                      timeout=180)
    r.raise_for_status()
    d = r.json()
    open(path, "wb").write(base64.b64decode(d["audio_base64"]))
    al = d.get("alignment") or {}
    words, cur, start = [], "", None
    for ch, s, e in zip(al.get("characters", []), al.get("character_start_times_seconds", []),
                        al.get("character_end_times_seconds", [])):
        if ch.isspace():
            if cur:
                words.append([start, end, cur]); cur = ""
            continue
        if not cur:
            start = s
        cur += ch; end = e
    if cur:
        words.append([start, end, cur])
    return words


def synth(text: str, path: str) -> list:
    """writes audio to path, returns word timings [[start, end, word], ...] (may be empty)"""
    if os.getenv("ELEVENLABS_API_KEY"):
        try:
            return _eleven(text, path)
        except Exception as e:
            print("ElevenLabs failed, using free voice:", e)
    last = None
    for v in EDGE_VOICES:
        try:
            words = _edge(text, path, v)
            if os.path.getsize(path) > 1000:
                return words
        except Exception as e:
            last = e
    raise RuntimeError(f"All TTS voices failed: {last}")


def clean(src: str, dst: str):
    """studio-style cleanup: remove rumble/hiss, tame harsh S sounds, even out volume"""
    chains = ["highpass=f=80,lowpass=f=13000,deesser=i=0.4,"
              "acompressor=threshold=0.1:ratio=3:attack=5:release=90:makeup=1.6,"
              "equalizer=f=3000:t=q:w=1.2:g=2",
              "highpass=f=80,acompressor=threshold=0.1:ratio=3:attack=5:release=90:makeup=1.6"]
    for af in chains:
        r = subprocess.run(["ffmpeg", "-y", "-v", "error", "-i", src, "-af", af, "-ar", "48000", "-ac", "1",
                            "-c:a", "pcm_s16le", dst], capture_output=True)
        if r.returncode == 0:
            return dst
    raise RuntimeError("voice clean failed: " + r.stderr.decode()[-500:])


def align(text: str, words: list, dur: float) -> list:
    """use TTS timings when available (with the script's punctuation), else estimate from text length"""
    tokens = text.split()
    if words:
        if len(words) == len(tokens):
            return [[w[0], w[1], t] for w, t in zip(words, tokens)]
        return words
    weights = [len(re.sub(r"\W", "", t)) + 2 for t in tokens]
    span, t, out = max(dur - 0.15, 0.5), 0.05, []
    for tok, wt in zip(tokens, weights):
        d = span * wt / sum(weights)
        out.append([t, t + d * 0.9, tok]); t += d
    return out


def duration(path: str) -> float:
    out = subprocess.check_output(["ffprobe", "-v", "error", "-show_entries", "format=duration",
                                   "-of", "default=nw=1:nk=1", path])
    return float(out.strip())
