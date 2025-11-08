from functools import lru_cache

from ..services.gemini_service import GeminiService
from ..services.elevenlabs_service import ElevenLabsService
from ..services.did_service import DIDService
from ..services.webgazer_service import WebGazerService
from .config import settings


@lru_cache()
def get_gemini_service() -> GeminiService:
    return GeminiService(api_key=settings.GEMINI_API_KEY)


@lru_cache()
def get_elevenlabs_service() -> ElevenLabsService:
    return ElevenLabsService(api_key=settings.ELEVENLABS_API_KEY)


@lru_cache()
def get_did_service() -> DIDService:
    return DIDService(api_key=settings.DID_API_KEY)


@lru_cache()
def get_webgazer_service() -> WebGazerService:
    return WebGazerService()
