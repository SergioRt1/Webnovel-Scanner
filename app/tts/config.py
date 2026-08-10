from __future__ import annotations

from dataclasses import dataclass


@dataclass
class TTSConfig:
    """
    Configuration for offline TTS with sherpa-onnx.

    ``model_path`` should normally be the **extracted model directory** from a
    sherpa-onnx TTS release tarball (for example a Piper VITS bundle or a
    Kokoro bundle). Optional fields override auto-discovery inside that folder.

    For Matcha / Kitten / other layouts, pass explicit paths; ``backend`` must
    not be ``\"auto\"``.
    """

    model_path: str
    voices: str | None = None
    tokens: str | None = None
    data_dir: str | None = None
    lexicon: str | None = None
    onnx_model: str | None = None
    """Explicit path to the main ``.onnx`` file (any supported backend)."""
    vits_model: str | None = None
    """Deprecated alias for ``onnx_model`` (kept for compatibility)."""
    kokoro_lexicon: str | None = None
    matcha_acoustic_model: str | None = None
    matcha_vocoder: str | None = None
    matcha_lexicon: str | None = None
    matcha_tokens: str | None = None
    matcha_data_dir: str | None = None
    kitten_model: str | None = None
    kitten_tokens: str | None = None
    kitten_data_dir: str | None = None
    speed: float = 1.0
    sid: int = 0
    split_by_chapter: bool = True
    output_dir: str = "Novels/audio"
    provider: str = "cpu"
    num_threads: int = 1
    max_num_sentences: int = -1
    tts_rule_fsts: str = ""
    silence_scale: float = 0.2
    debug: bool = False
    backend: str = "auto"
    """One of: auto, vits, kokoro, matcha, kitten."""
