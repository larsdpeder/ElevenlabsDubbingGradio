"""Text-to-Speech provider abstraction.

The dubbing pipeline in ``dub.py`` uses ElevenLabs' *dubbing* API (video in,
dubbed video out). That is a different capability from plain *text-to-speech*,
so it is intentionally left alone.

This module adds a small, provider-agnostic TTS interface so the Gradio app can
turn typed text into an audio file without caring which backend produced it.
Today there is a single backend, 60db (https://docs.60db.ai), spoken over its
WebSocket protocol. Adding another provider (e.g. ElevenLabs TTS) later is just
another ``TTSProvider`` subclass plus an entry in ``get_tts_provider``.
"""

import os
import json
import uuid
import wave
import base64
from abc import ABC, abstractmethod
from typing import Optional

import websocket  # from the `websocket-client` package

# 60db's documented default voice (see docs.60db.ai/websocket-api/tts).
SIXTYDB_DEFAULT_VOICE = "fbb75ed2-975a-40c7-9e06-38e30524a9a1"


class TTSProvider(ABC):
    """Turn text into a mono PCM/WAV audio file on disk.

    Implementations must be interchangeable: callers pass text plus a handful of
    common voice controls and get back the path to a finished audio file.
    """

    name: str = "tts"

    @abstractmethod
    def synthesize(
        self,
        text: str,
        output_path: str,
        *,
        voice_id: Optional[str] = None,
        speed: float = 1.0,
        stability: int = 50,
        similarity: int = 75,
    ) -> str:
        """Synthesize ``text`` and write the audio to ``output_path``.

        Returns the path that was written.
        """
        raise NotImplementedError


class SixtyDBTTSProvider(TTSProvider):
    """60db TTS over the WebSocket streaming API.

    Protocol (docs.60db.ai/websocket-api/tts):
        connect ws://.../ws/tts?apiKey=...
          -> server sends {"connection_established": {...}}
        send {"create_context": {context_id, voice_id, audio_config, speed, ...}}
        send {"send_text":     {context_id, text}}
        send {"flush_context": {context_id}}
          <- {"audio_chunk":     {context_id, audioContent: <base64>}}  (repeated)
          <- {"flush_completed": {context_id}}
        send {"close_context":  {context_id}}
          <- {"context_closed":  {context_id}}

    We request ``LINEAR16`` (raw 16-bit signed PCM), which the docs note is
    safely concatenable, so the chunks are joined and wrapped in a WAV header.
    """

    name = "60db"

    # LINEAR16 supports 8k / 16k / 24k / 48k; 24k is a good speech default.
    _SAMPLE_WIDTH_BYTES = 2  # 16-bit
    _CHANNELS = 1

    def __init__(
        self,
        api_key: Optional[str] = None,
        ws_url: Optional[str] = None,
        sample_rate: int = 24000,
        timeout: int = 60,
    ):
        self.api_key = api_key or os.getenv("SIXTYDB_API_KEY")
        if not self.api_key:
            raise ValueError(
                "SIXTYDB_API_KEY is not set. Add it to your .env file to use 60db TTS."
            )
        # The docs show ws://, but the REST host is served over TLS; default to
        # the secure scheme and allow an override for non-TLS / staging hosts.
        self.ws_url = ws_url or os.getenv("SIXTYDB_WS_URL", "wss://api.60db.ai/ws/tts")
        self.sample_rate = sample_rate
        self.timeout = timeout

    def _connect(self) -> "websocket.WebSocket":
        sep = "&" if "?" in self.ws_url else "?"
        url = f"{self.ws_url}{sep}apiKey={self.api_key}"
        return websocket.create_connection(url, timeout=self.timeout)

    def synthesize(
        self,
        text: str,
        output_path: str,
        *,
        voice_id: Optional[str] = None,
        speed: float = 1.0,
        stability: int = 50,
        similarity: int = 75,
    ) -> str:
        if not text or not text.strip():
            raise ValueError("Cannot synthesize empty text.")

        context_id = str(uuid.uuid4())
        ws = self._connect()
        pcm = bytearray()
        try:
            ws.send(json.dumps({
                "create_context": {
                    "context_id": context_id,
                    "voice_id": voice_id or SIXTYDB_DEFAULT_VOICE,
                    "audio_config": {
                        "audio_encoding": "LINEAR16",
                        "sample_rate_hertz": self.sample_rate,
                    },
                    "speed": speed,
                    "stability": stability,
                    "similarity": similarity,
                }
            }))
            ws.send(json.dumps({"send_text": {"context_id": context_id, "text": text}}))
            ws.send(json.dumps({"flush_context": {"context_id": context_id}}))

            # Read until the flush for our context is complete. Other control
            # messages (e.g. connection_established) are simply ignored.
            while True:
                message = json.loads(ws.recv())
                if "audio_chunk" in message:
                    pcm += base64.b64decode(message["audio_chunk"]["audioContent"])
                elif "flush_completed" in message:
                    break
                elif "error" in message:
                    raise RuntimeError(
                        message["error"].get("message", "Unknown 60db TTS error")
                    )

            # Best-effort graceful close; ignore whatever the server echoes back.
            try:
                ws.send(json.dumps({"close_context": {"context_id": context_id}}))
            except Exception:
                pass
        finally:
            ws.close()

        if not pcm:
            raise RuntimeError("60db returned no audio for the given text.")

        self._write_wav(output_path, bytes(pcm))
        return output_path

    def _write_wav(self, path: str, pcm_bytes: bytes) -> None:
        with wave.open(path, "wb") as wav_file:
            wav_file.setnchannels(self._CHANNELS)
            wav_file.setsampwidth(self._SAMPLE_WIDTH_BYTES)
            wav_file.setframerate(self.sample_rate)
            wav_file.writeframes(pcm_bytes)


def get_tts_provider(name: str = "60db") -> TTSProvider:
    """Return a TTS provider by name. Central place to wire new backends in."""
    providers = {
        "60db": SixtyDBTTSProvider,
    }
    key = name.lower()
    if key not in providers:
        raise ValueError(
            f"Unknown TTS provider '{name}'. Available: {', '.join(providers)}"
        )
    return providers[key]()
