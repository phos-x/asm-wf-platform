"""
MUSDB18 Preprocessing Script (Dynamic Path Version)

This script:
  - Validates the raw MUSDB18 dataset structure
  - Decodes .mp4 STEMS files into WAV stems using stempeg
  - Writes mixture, drums, bass, other, vocals into per-track folders
  - Builds train/valid folder structure for model training
  - Performs post-process validation

Security & Best Practices:
  - No shell execution
  - No unsafe path concatenation
  - Full input validation
  - Deterministic output structure
  - Works from ANY folder (scripts/, tools/, etc.)
"""

from __future__ import annotations

import shutil
from pathlib import Path
from typing import List

import stempeg
import soundfile as sf


# ---------------------------------------------------------------------------
# Validation helpers
# ---------------------------------------------------------------------------

def validate_raw_musdb(raw_root: Path) -> None:
    """Validate MUSDB18 raw folder structure."""
    if not raw_root.exists():
        raise FileNotFoundError(f"Raw MUSDB18 folder not found: {raw_root}")

    train_dir = raw_root / "train"
    test_dir = raw_root / "test"

    if not train_dir.is_dir():
        raise FileNotFoundError(f"Missing MUSDB18 'train' folder at: {train_dir}")
    if not test_dir.is_dir():
        raise FileNotFoundError(f"Missing MUSDB18 'test' folder at: {test_dir}")

    if not any(train_dir.glob("*.mp4")):
        raise RuntimeError("No .mp4 STEMS files found in MUSDB18 train folder")
    if not any(test_dir.glob("*.mp4")):
        raise RuntimeError("No .mp4 STEMS files found in MUSDB18 test folder")


def validate_processed_dataset(out_root: Path) -> None:
    """Validate that the processed dataset contains expected WAV stems."""
    required_stems = {
        "mixture.wav",
        "drums.wav",
        "bass.wav",
        "other.wav",
        "vocals.wav",
    }

    for split in ["train", "valid"]:
        split_dir = out_root / split
        if not split_dir.is_dir():
            raise RuntimeError(f"Missing processed split folder: {split_dir}")

        for track_dir in split_dir.iterdir():
            if not track_dir.is_dir():
                continue

            stems = {f.name for f in track_dir.glob("*.wav")}
            missing = required_stems - stems
            if missing:
                raise RuntimeError(
                    f"Track '{track_dir.name}' missing stems: {missing}"
                )


# ---------------------------------------------------------------------------
# Core extraction logic
# ---------------------------------------------------------------------------

STEM_NAMES = ["mixture", "drums", "bass", "other", "vocals"]

def safe_name(name: str) -> str:
    """Convert track folder name into a safe, standardized filename."""
    return (
        name.lower()
        .replace(" ", "_")
        .replace("-", "_")
        .replace("__", "_")
        .strip()
    )

def extract_stems(mp4_path: Path, out_dir: Path) -> None:
    """Decode a MUSDB18 .mp4 STEMS file into WAV files."""
    out_dir.mkdir(parents=True, exist_ok=True)

    stems, rate = stempeg.read_stems(str(mp4_path))

    for idx, name in enumerate(STEM_NAMES):
        wav_path = out_dir / f"{name}.wav"
        sf.write(wav_path, stems[idx], rate)


def process_split(raw_split: Path, out_split: Path) -> None:
    """Process all tracks in a MUSDB18 split (train/test)."""
    out_split.mkdir(parents=True, exist_ok=True)

    for mp4_file in raw_split.glob("*.mp4"):
        track_name = safe_name(mp4_file.stem.replace(".stem", ""))
        track_out = out_split / track_name
        extract_stems(mp4_file, track_out)


# ---------------------------------------------------------------------------
# Main preprocessing entrypoint
# ---------------------------------------------------------------------------

def preprocess_musdb18(raw_root: Path, out_root: Path) -> None:
    """
    Full MUSDB18 preprocessing pipeline.
    Works from ANY directory (scripts/, tools/, etc.)
    """
    print(f"Validating raw MUSDB18 dataset at: {raw_root}")
    validate_raw_musdb(raw_root)

    # Clean output folder
    if out_root.exists():
        shutil.rmtree(out_root)
    out_root.mkdir(parents=True, exist_ok=True)

    print("Processing training split...")
    process_split(raw_root / "train", out_root / "train")

    print("Processing validation split...")
    process_split(raw_root / "test", out_root / "valid")

    print("Validating processed dataset...")
    validate_processed_dataset(out_root)

    print("\nMUSDB18 preprocessing complete.")
    print(f"Processed dataset stored at: {out_root}")


# ---------------------------------------------------------------------------
# CLI wrapper
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Preprocess MUSDB18 dataset")
    parser.add_argument(
        "--raw_root",
        required=True,
        type=Path,
        help="Path to raw MUSDB18 folder containing train/ and test/",
    )
    parser.add_argument(
        "--out_root",
        required=True,
        type=Path,
        help="Output folder for processed dataset",
    )

    args = parser.parse_args()
    preprocess_musdb18(args.raw_root, args.out_root)
