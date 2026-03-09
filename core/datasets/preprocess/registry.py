"""
Preprocessing registry.

Maps dataset preprocessing keys to concrete functions.
"""

from __future__ import annotations
from typing import Callable, Dict, Any

from . import mel, pitch, noise


PREPROCESSORS: Dict[str, Callable[[str, str, Dict[str, Any]], None]] = {
    "mel": mel.run,
    "pitch": pitch.run,
    "noise": noise.run,
}


def get_preprocessor(name: str) -> Callable[[str, str, Dict[str, Any]], None]:
    try:
        return PREPROCESSORS[name]
    except KeyError as exc:
        raise KeyError(f"Unknown preprocessor: {name}") from exc
