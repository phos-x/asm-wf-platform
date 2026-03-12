#!/usr/bin/env python3
"""
Generate per-model requirements.txt files from Python imports.

Scans `core/models/<model>/` for `.py` files, extracts imports via AST,
and writes a requirements.txt containing only third-party packages.

Stdlib modules (e.g. abc, pathlib, os, warnings) are excluded.
Missing modules (e.g. numpy not installed) are kept.
"""

from __future__ import annotations

import argparse
import ast
import sys
import sysconfig
from pathlib import Path
from typing import Iterable, Set, Optional

VENV_DIR_NAMES = {"venv", ".venv", "env", ".env", "venv3", "venv36"}


def iter_imported_modules(path: Path) -> Iterable[str]:
    for py_file in path.rglob("*.py"):
        try:
            tree = ast.parse(py_file.read_text(encoding="utf-8"), filename=str(py_file))
        except (SyntaxError, UnicodeDecodeError):
            continue
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    yield alias.name.split(".")[0]
            elif isinstance(node, ast.ImportFrom):
                if node.module:
                    yield node.module.split(".")[0]


def get_stdlib_dirs() -> Set[Path]:
    """Return the standard-library directories for this interpreter."""
    out: Set[Path] = set()
    for key in ("stdlib", "platstdlib"):
        try:
            out.add(Path(sysconfig.get_path(key)).resolve())
        except Exception:
            continue
    return out


def is_stdlib_module(name: str, stdlib_names: Set[str], builtin_names: Set[str]) -> bool:
    if name in builtin_names:
        return True
    if name in stdlib_names:
        return True
    return False


def is_local_project_module(origin: Path, project_root: Path) -> bool:
    """
    Return True if `origin` is inside the project root and not inside a venv.
    """
    try:
        rel = origin.resolve().relative_to(project_root.resolve())
    except Exception:
        return False

    if not rel.parts:
        return False

    if rel.parts[0] in VENV_DIR_NAMES:
        return False

    return True


def should_include_module(
    mod: str,
    project_root: Path,
    stdlib_names: Set[str],
    builtin_names: Set[str],
    stdlib_dirs: Set[Path],
) -> bool:
    if not mod or mod.startswith(".") or mod.startswith("__"):
        return False

    if is_stdlib_module(mod, stdlib_names, builtin_names):
        return False

    try:
        spec = __import__("importlib.util").find_spec(mod)
    except Exception:
        spec = None

    if spec is None:
        # Missing in the current environment → likely third-party
        return True

    origin = getattr(spec, "origin", None)
    if not origin:
        # Namespace pkg / built-in: keep to be safe (pip cannot install builtins anyway)
        return False

    origin_path = Path(origin).resolve()
    if origin_path == Path("built-in"):
        return False

    if any(stdlib_dir in origin_path.parents or origin_path == stdlib_dir for stdlib_dir in stdlib_dirs):
        return False

    if is_local_project_module(origin_path, project_root):
        return False

    return True


def main() -> int:
    parser = argparse.ArgumentParser(description="Generate per-model requirements.txt")
    parser.add_argument(
        "--project-root",
        type=Path,
        default=Path(__file__).resolve().parents[1],
        help="Project root directory",
    )
    parser.add_argument(
        "--models-subdir",
        type=str,
        default="models",
        help="Subdirectory under project root containing model folders",
    )
    args = parser.parse_args()

    project_root = args.project_root.resolve()
    model_root = (project_root / args.models_subdir).resolve()

    if not model_root.is_dir():
        print(f"Error: model directory not found: {model_root}", file=sys.stderr)
        return 1

    builtin_names = set(sys.builtin_module_names)
    try:
        stdlib_names = set(sys.stdlib_module_names)
    except AttributeError:
        stdlib_names = set()

    stdlib_dirs = get_stdlib_dirs()

    for folder in sorted(model_root.iterdir()):
        if not folder.is_dir():
            continue

        imports = set(iter_imported_modules(folder))
        filtered: Set[str] = set()
        for mod in imports:
            if should_include_module(
                mod,
                project_root=project_root,
                stdlib_names=stdlib_names,
                builtin_names=builtin_names,
                stdlib_dirs=stdlib_dirs,
            ):
                filtered.add(mod)

        requirements_path = folder / "requirements.txt"
        sorted_deps = sorted(filtered)

        tmp = requirements_path.with_suffix(".txt.tmp")
        tmp.write_text("\n".join(sorted_deps) + ("\n" if sorted_deps else ""))
        tmp.replace(requirements_path)

        print(f"Generated: {requirements_path} ({len(sorted_deps)} deps)")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())