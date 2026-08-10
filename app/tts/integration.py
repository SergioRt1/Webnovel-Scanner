from __future__ import annotations

from collections.abc import Callable
from pathlib import Path

import soundfile as sf
import sherpa_onnx

from app.tts.config import TTSConfig
from app.tts.sherpa_builder import build_offline_tts_config
from app.core.cancel import CancelToken
from app.core.events import ProgressEvent
from app.models.entities import Novel

ProgressCallback = Callable[[ProgressEvent], None]

MAX_CHUNK_LENGTH = 1000

class TTSProcessor:
    """
    Offline novel TTS using sherpa-onnx.
    """

    def __init__(self, config: TTSConfig):
        self.config = config
        self._engine: sherpa_onnx.OfflineTts | None = None
        self._load_model()

    def _load_model(self) -> None:
        tts_config = build_offline_tts_config(self.config)
        if not tts_config.validate():
            raise ValueError(
                "sherpa-onnx rejected this configuration. "
                "Check model_path, tokens, data_dir / voices, and backend."
            )
        self._engine = sherpa_onnx.OfflineTts(tts_config)

    def synthesize_to_file(
        self,
        text: str,
        output_path: str | Path,
        *,
        cancel_token: CancelToken | None = None,
    ) -> None:
        """Synthesize arbitrary text to a WAV file (16-bit PCM)."""
        self._synthesize_to_file(text, str(output_path), cancel_token)

    def export_novel_to_audio(
        self,
        novel: Novel,
        progress_callback: ProgressCallback | None = None,
        cancel_token: CancelToken | None = None,
    ) -> list[str]:
        """
        Convert a novel to one or more WAV files.
        """
        if self._engine is None:
            raise RuntimeError("TTS engine is not initialized.")

        base_dir = Path(self.config.output_dir) / novel.safe_title
        base_dir.mkdir(parents=True, exist_ok=True)

        chapters = novel.chapter_list
        total = len(chapters)

        if cancel_token is not None:
            cancel_token.raise_if_cancelled()

        if not self.config.split_by_chapter:
            parts: list[str] = []
            for ch in chapters:
                t = (ch.content or "").strip()
                if t:
                    parts.append(t)
            merged = "\n\n".join(parts).strip()
            if not merged:
                return []
            if progress_callback:
                progress_callback(ProgressEvent(current=1, total=1, message=f"TTS: {novel.safe_title}"))
            out = base_dir / f"{novel.safe_title}.wav"
            self._synthesize_to_file(merged, str(out), cancel_token)
            return [str(out)]

        output_paths: list[str] = []
        for idx, chapter in enumerate(chapters, start=1):
            if cancel_token is not None:
                cancel_token.raise_if_cancelled()

            if progress_callback:
                progress_callback(ProgressEvent(current=idx, total=total, message=f"TTS: {chapter.title}"))

            text = (chapter.content or "").strip()
            if not text:
                continue

            output_file = base_dir / f"{idx:04d}_{chapter.safe_title}.wav"
            self._synthesize_to_file(text, str(output_file), cancel_token)
            output_paths.append(str(output_file))

        return output_paths

    def _chunk_text(self, text: str) -> list[str]:
        import re
        paragraphs = [p.strip() for p in re.split(r'\n+', text) if p.strip()]
        chunks = []
        for p in paragraphs:
            if len(p) < MAX_CHUNK_LENGTH:
                chunks.append(p)
            else:
                sentences = re.split(r'(?<=[.!?])\s+', p)
                curr = ""
                for s in sentences:
                    if len(curr) + len(s) < MAX_CHUNK_LENGTH:
                        curr += s + " "
                    else:
                        if curr:
                            chunks.append(curr.strip())
                        curr = s + " "
                if curr:
                    chunks.append(curr.strip())
        return chunks

    def _synthesize_to_file(
        self,
        text: str,
        output_path: str,
        cancel_token: CancelToken | None = None,
    ) -> None:
        if self._engine is None:
            raise RuntimeError("TTS engine is not initialized.")

        if cancel_token is not None:
            cancel_token.raise_if_cancelled()

        gen = sherpa_onnx.GenerationConfig()
        gen.sid = self.config.sid
        gen.speed = self.config.speed
        gen.silence_scale = self.config.silence_scale

        chunks = self._chunk_text(text)

        all_samples = []
        sample_rate = None

        for chunk in chunks:
            if cancel_token is not None:
                cancel_token.raise_if_cancelled()
            
            # Skip empty or whitespace-only chunks
            if not chunk.strip():
                continue

            audio = self._engine.generate(chunk, gen)
            
            if len(audio.samples) > 0:
                all_samples.extend(audio.samples)
                if sample_rate is None:
                    sample_rate = audio.sample_rate

        if len(all_samples) == 0:
            raise RuntimeError(
                "TTS produced empty audio. Check stderr from sherpa-onnx, "
                "model assets, and input text."
            )

        sf.write(
            output_path,
            all_samples,
            samplerate=sample_rate,
            subtype="PCM_16",
        )

__all__ = ["TTSConfig", "TTSProcessor", "ProgressCallback"]
