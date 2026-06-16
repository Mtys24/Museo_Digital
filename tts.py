import os
import hashlib
import asyncio
from pathlib import Path

import edge_tts

AUDIO_DIR = Path("audio_cache")
AUDIO_DIR.mkdir(exist_ok=True)


def _hash_text(text: str) -> str:
    return hashlib.md5(text.encode("utf-8")).hexdigest()


def _clean_old_files(max_files: int = 50):
    files = sorted(AUDIO_DIR.iterdir(), key=os.path.getmtime)
    for f in files[:-max_files]:
        f.unlink(missing_ok=True)


def generate_audio(text: str, voice_name: str) -> str:
    text = text.strip()
    if not text:
        return ""

    filename = f"{_hash_text(text)}_{voice_name.replace('/', '_')}.mp3"
    filepath = AUDIO_DIR / filename

    if filepath.exists():
        return str(filepath)

    async def _generate():
        communicate = edge_tts.Communicate(text, voice_name)
        await communicate.save(str(filepath))

    asyncio.run(_generate())
    _clean_old_files()
    return str(filepath)
