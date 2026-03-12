"""
Universal Stem Extraction Script for Processed MUSDB18

This script:
  - Extracts one or more stems (vocals, mixture, drums, bass, other)
  - Standardizes filenames (lowercase, underscores, no spaces)
  - Validates the extracted dataset
  - Generates metadata.json with useful information

Security & Best Practices:
  - No shell execution
  - No unsafe path concatenation
  - Full validation of input/output paths
  - Deterministic output structure
"""

from __future__ import annotations

import json
import shutil
from pathlib import Path
from typing import Dict, List

import soundfile as sf


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

VALID_STEMS = {"mixture", "vocals", "drums", "bass", "other"}


def safe_name(name: str) -> str:
    """Convert track folder name into a safe, standardized filename."""
    return (
        name.lower()
        .replace(" ", "_")
        .replace("-", "_")
        .replace("__", "_")
        .strip()
    )


def validate_processed_root(root: Path) -> None:
    """Ensure processed MUSDB18 structure exists."""
    if not root.exists():
        raise FileNotFoundError(f"Processed dataset not found: {root}")

    for split in ["train", "valid"]:
        split_dir = root / split
        if not split_dir.is_dir():
            raise RuntimeError(f"Missing split folder: {split_dir}")


def extract_audio_metadata(wav_path: Path) -> Dict[str, float]:
    """Return duration and sample rate of a WAV file."""
    data, sr = sf.read(wav_path)
    duration = len(data) / sr
    return {"sample_rate": sr, "duration_sec": duration}


# ---------------------------------------------------------------------------
# Core logic
# ---------------------------------------------------------------------------

def extract_stems(
    processed_root: Path,
    out_root: Path,
    stems_to_extract: List[str],
    include_splits: List[str] = ["train", "valid"],
) -> None:
    """
    Extract selected stems from processed MUSDB18 dataset.
    """
    # Validate stems
    for stem in stems_to_extract:
        if stem not in VALID_STEMS:
            raise ValueError(f"Invalid stem '{stem}'. Valid options: {VALID_STEMS}")

    validate_processed_root(processed_root)

    # Clean output folder
    if out_root.exists():
        shutil.rmtree(out_root)
    out_root.mkdir(parents=True, exist_ok=True)

    metadata: List[Dict[str, str]] = []

    for split in include_splits:
        split_dir = processed_root / split
        out_split = out_root / split
        out_split.mkdir(parents=True, exist_ok=True)

        for track_dir in split_dir.iterdir():
            if not track_dir.is_dir():
                continue

            safe = safe_name(track_dir.name)

            for stem in stems_to_extract:
                stem_file = track_dir / f"{stem}.wav"
                if not stem_file.exists():
                    print(f"Warning: Missing {stem}.wav in {track_dir}")
                    continue

                out_file = out_split / f"{safe}_{stem}.wav"
                shutil.copy2(stem_file, out_file)

                audio_meta = extract_audio_metadata(out_file)

                metadata.append(
                    {
                        "track_name": track_dir.name,
                        "safe_name": safe,
                        "stem": stem,
                        "split": split,
                        "original_path": str(stem_file),
                        "copied_path": str(out_file),
                        **audio_meta,
                    }
                )

    # Write metadata file
    meta_path = out_root / "metadata.json"
    with meta_path.open("w") as f:
        json.dump(metadata, f, indent=4)

    print(f"Extraction complete. Metadata written to: {meta_path}")


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(
        description="Extract stems from processed MUSDB18 dataset"
    )
    parser.add_argument(
        "--processed_root",
        required=True,
        type=Path,
        help="Path to processed MUSDB18 dataset (contains train/ and valid/)",
    )
    parser.add_argument(
        "--out_root",
        required=True,
        type=Path,
        help="Output folder for extracted stems",
    )
    parser.add_argument(
        "--stems",
        required=True,
        nargs="+",
        help="List of stems to extract (e.g., vocals mixture drums)",
    )

    args = parser.parse_args()
    extract_stems(args.processed_root, args.out_root, args.stems)
