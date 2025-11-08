"""Dummy ElevenLabs TTS service wrapper.

synthesize_voice(text) -> returns a dict with audio_url and metadata.
For local testing we generate a placeholder file path instead of calling the external API.
"""
from pathlib import Path
from typing import Dict
import uuid


class ElevenLabsService:
    def __init__(self, api_key: str | None = None):
        self.api_key = api_key
        # write TTS assets to the static directory so they are servable at /static/tts
        self._out_dir = Path("./backend/static/tts")
        self._out_dir.mkdir(parents=True, exist_ok=True)

    def synthesize_voice(self, question_text: str, voice: str = "alloy") -> Dict[str, str]:
        """Simulate TTS output by writing a tiny text file into backend/static/tts and returning
        an HTTP-accessible path under /static/tts.
        """
        filename = f"tts_{uuid.uuid4().hex[:8]}.txt"
        path = self._out_dir / filename
        path.write_text(f"TTS placeholder for: {question_text}\nvoice={voice}\n")
        # return relative URL that frontend can fetch from the same host: /static/tts/<filename>
        return {"audio_url": f"/static/tts/{filename}", "format": "text-placeholder"}
