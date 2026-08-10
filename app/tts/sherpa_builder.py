from __future__ import annotations

import warnings
from pathlib import Path
from typing import Literal

from app.tts.config import TTSConfig

Backend = Literal["vits", "kokoro", "matcha", "kitten"]


def _root_and_onnx_hint(model_path: str) -> tuple[Path, Path | None]:
    p = Path(model_path).expanduser().resolve()
    if p.is_file() and p.suffix.lower() == ".onnx":
        return p.parent, p
    return p, None


def _onnx_explicit(cfg: TTSConfig) -> str | None:
    return cfg.onnx_model or cfg.vits_model


def _pick_onnx(root: Path, explicit: str | None) -> Path:
    if explicit:
        q = Path(explicit).expanduser().resolve()
        if not q.is_file():
            raise FileNotFoundError(f"onnx model file not found: {q}")
        return q
    onxs = sorted(root.glob("*.onnx"))
    if not onxs:
        raise FileNotFoundError(f"No .onnx file found under {root}")
    preferred = root / "model.onnx"
    if preferred.is_file():
        return preferred
    if len(onxs) > 1:
        warnings.warn(
            f"Multiple .onnx files in {root}; using {onxs[0].name}. "
            "Set TTSConfig.onnx_model (or place model.onnx) to disambiguate.",
            stacklevel=2,
        )
    return onxs[0]


def _detect_backend(cfg: TTSConfig, root: Path) -> Backend:
    b = (cfg.backend or "auto").lower()
    if b not in ("auto", "vits", "kokoro", "matcha", "kitten"):
        raise ValueError(f"Unknown backend: {cfg.backend!r}")
    if b != "auto":
        return b  # type: ignore[return-value]
    if cfg.matcha_acoustic_model or cfg.matcha_vocoder:
        return "matcha"
    if cfg.kitten_model:
        return "kitten"
    voices_path = cfg.voices or str(root / "voices.bin")
    if Path(voices_path).is_file():
        return "kokoro"
    return "vits"


def build_offline_tts_config(cfg: TTSConfig):
    import sherpa_onnx as so

    root, onnx_hint = _root_and_onnx_hint(cfg.model_path)
    if not root.exists():
        raise FileNotFoundError(f"model_path does not exist: {cfg.model_path!r}")
    if not root.is_dir():
        raise NotADirectoryError(
            f"model_path must be a directory or an .onnx file; got {cfg.model_path!r}"
        )

    backend = _detect_backend(cfg, root)
    tokens = cfg.tokens or str(root / "tokens.txt")
    data_dir = cfg.data_dir or str(root / "espeak-ng-data")

    vits = so.OfflineTtsVitsModelConfig(model="", lexicon="", data_dir="", tokens="")
    kokoro = so.OfflineTtsKokoroModelConfig(
        model="", voices="", tokens="", data_dir="", lexicon=""
    )
    matcha = so.OfflineTtsMatchaModelConfig(
        acoustic_model="", vocoder="", lexicon="", tokens="", data_dir=""
    )
    kitten = so.OfflineTtsKittenModelConfig(
        model="", voices="", tokens="", data_dir=""
    )

    onnx_pick = _onnx_explicit(cfg)

    if backend == "vits":
        onnx = onnx_hint or _pick_onnx(root, onnx_pick)
        vits = so.OfflineTtsVitsModelConfig(
            model=str(onnx),
            lexicon=cfg.lexicon or "",
            data_dir=data_dir if Path(data_dir).is_dir() else "",
            tokens=tokens,
        )
    elif backend == "kokoro":
        onnx = onnx_hint or _pick_onnx(root, onnx_pick)
        voices = cfg.voices or str(root / "voices.bin")
        if not Path(voices).is_file():
            raise FileNotFoundError(
                f"Kokoro expects voices.bin at {voices}. "
                "Pass TTSConfig.voices=... if it lives elsewhere."
            )
        kokoro = so.OfflineTtsKokoroModelConfig(
            model=str(onnx),
            voices=voices,
            tokens=tokens,
            data_dir=data_dir,
            lexicon=cfg.kokoro_lexicon or "",
        )
    elif backend == "matcha":
        if not cfg.matcha_acoustic_model or not cfg.matcha_vocoder:
            raise ValueError(
                "Matcha backend requires matcha_acoustic_model and matcha_vocoder."
            )
        matcha = so.OfflineTtsMatchaModelConfig(
            acoustic_model=cfg.matcha_acoustic_model,
            vocoder=cfg.matcha_vocoder,
            lexicon=cfg.matcha_lexicon or "",
            tokens=cfg.matcha_tokens or tokens,
            data_dir=cfg.matcha_data_dir or (data_dir if Path(data_dir).is_dir() else ""),
        )
    elif backend == "kitten":
        if not cfg.kitten_model:
            raise ValueError("Kitten backend requires kitten_model.")
        voices = cfg.voices or str(root / "voices.bin")
        if not Path(voices).is_file():
            raise FileNotFoundError(
                f"Kitten expects voices.bin at {voices}. "
                "Pass TTSConfig.voices=... if it lives elsewhere."
            )
        kitten = so.OfflineTtsKittenModelConfig(
            model=cfg.kitten_model,
            voices=voices,
            tokens=tokens,
            data_dir=data_dir,
        )

    tts_config = so.OfflineTtsConfig(
        model=so.OfflineTtsModelConfig(
            vits=vits,
            matcha=matcha,
            kokoro=kokoro,
            kitten=kitten,
            provider=cfg.provider,
            debug=cfg.debug,
            num_threads=cfg.num_threads,
        ),
        rule_fsts=cfg.tts_rule_fsts,
        max_num_sentences=cfg.max_num_sentences,
    )
    return tts_config
