"""Step 2: narration -> mp3 per scene.
Uses ElevenLabs if ELEVENLABS_API_KEY is set (most natural, paid), otherwise free Microsoft Edge TTS
with a natural 'Multilingual' neural voice (falls back to a standard voice if unavailable)."""
import asyncio, os, subprocess
import requests

EDGE_VOICES = [os.getenv("EDGE_VOICE", "en-US-AndrewMultilingualNeural"), "en-US-AndrewNeural", "en-US-GuyNeural"]
ELEVEN_VOICE = os.getenv("ELEVEN_VOICE_ID", "pNInz6obpgDQGcFmaJgB")  # "Adam" premade voice


def _eleven(text, path):
    r = requests.post(f"https://api.elevenlabs.io/v1/text-to-speech/{ELEVEN_VOICE}",
                      headers={"xi-api-key": os.environ["ELEVENLABS_API_KEY"], "accept": "audio/mpeg"},
                      json={"text": text, "model_id": "eleven_multilingual_v2",
                            "voice_settings": {"stability": 0.45, "similarity_boost": 0.8, "style": 0.3}},
                      timeout=120)
    r.raise_for_status()
    open(path, "wb").write(r.content)


async def _edge(text, path, voice):
    import edge_tts
    await edge_tts.Communicate(text, voice, rate="+4%").save(path)


def synth(text: str, path: str) -> float:
    if os.getenv("ELEVENLABS_API_KEY"):
        try:
            _eleven(text, path)
            return duration(path)
        except Exception as e:
            print("ElevenLabs failed, using free voice:", e)
    last = None
    for v in EDGE_VOICES:
        try:
            # run in its own thread so it works even when another event loop (Playwright) is active
            import threading
            err = []
            def job():
                try:
                    asyncio.run(_edge(text, path, v))
                except Exception as ex:
                    err.append(ex)
            t = threading.Thread(target=job); t.start(); t.join()
            if err:
                raise err[0]
            if os.path.getsize(path) > 1000:
                return duration(path)
        except Exception as e:
            last = e
    raise RuntimeError(f"All TTS voices failed: {last}")


def duration(path: str) -> float:
    out = subprocess.check_output(
        ["ffprobe", "-v", "error", "-show_entries", "format=duration",
         "-of", "default=nw=1:nk=1", path])
    return float(out.strip())
