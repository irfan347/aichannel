"""Step 2: narration -> mp3 per scene (free Microsoft Edge TTS)."""
import asyncio, subprocess
import edge_tts

VOICE = "en-US-AndrewNeural"  # try en-US-AriaNeural, en-GB-RyanNeural


async def _tts(text, path, voice):
    await edge_tts.Communicate(text, voice, rate="+5%").save(path)


def synth(text: str, path: str, voice: str = VOICE) -> float:
    asyncio.run(_tts(text, path, voice))
    return duration(path)


def duration(path: str) -> float:
    out = subprocess.check_output(
        ["ffprobe", "-v", "error", "-show_entries", "format=duration",
         "-of", "default=nw=1:nk=1", path])
    return float(out.strip())
