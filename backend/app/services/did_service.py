"""D-ID talking-head video generation wrapper (stub).

generate_avatar_video(audio_url) -> returns a dict with video_url and job_id.
The real integration would call D-ID's API and provide the ElevenLabs audio asset.
"""
from pathlib import Path
from typing import Dict
import uuid


class DIDService:
    def __init__(self, api_key: str | None = None):
        self.api_key = api_key
        # write video placeholders to static directory so they can be served
        self._out_dir = Path("./backend/static/did")
        self._out_dir.mkdir(parents=True, exist_ok=True)

    def generate_avatar_video(self, audio_url: str, avatar_id: str | None = None) -> Dict[str, str]:
        # create a placeholder mp4 file (empty) and return a path under /static/did
        filename = f"video_{uuid.uuid4().hex[:8]}.mp4"
        path = self._out_dir / filename
        path.write_bytes(b"")
        return {"video_url": f"/static/did/{filename}", "status": "ready"}
