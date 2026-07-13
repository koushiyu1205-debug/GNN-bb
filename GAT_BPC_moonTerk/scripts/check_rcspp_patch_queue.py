#!/usr/bin/env python3
"""Validate the optional rcspp patch queue against its pinned upstream tree."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import subprocess
import sys


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_MANIFEST = ROOT / "third_party" / "patches" / "rcspp" / "manifest.json"


def _git(source: Path, *args: str) -> str:
    completed = subprocess.run(
        ["git", "-C", str(source), *args],
        text=True,
        capture_output=True,
        check=False,
    )
    if completed.returncode != 0:
        raise RuntimeError(completed.stderr.strip() or completed.stdout.strip())
    return completed.stdout.strip()


def check_patch_queue(source: Path, manifest_path: Path) -> None:
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    expected_commit = str(manifest["upstream_commit"])
    actual_commit = _git(source, "rev-parse", "HEAD")
    if actual_commit != expected_commit:
        raise RuntimeError(
            f"rcspp checkout mismatch: expected {expected_commit}, got {actual_commit}"
        )
    patch_root = manifest_path.parent
    for row in manifest.get("patches", []):
        patch_path = patch_root / str(row["file"])
        for blob in row.get("upstream_blobs", []):
            relative_path = str(blob["path"])
            expected_blob = str(blob["git_blob_hash"])
            actual_blob = _git(source, "hash-object", relative_path)
            if actual_blob != expected_blob:
                raise RuntimeError(
                    f"upstream blob mismatch for {relative_path}: "
                    f"expected {expected_blob}, got {actual_blob}"
                )
        completed = subprocess.run(
            ["git", "-C", str(source), "apply", "--check", str(patch_path)],
            text=True,
            capture_output=True,
            check=False,
        )
        if completed.returncode != 0:
            raise RuntimeError(
                f"git apply --check failed for {patch_path.name}: {completed.stderr.strip()}"
            )


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--source", type=Path, required=True)
    parser.add_argument("--manifest", type=Path, default=DEFAULT_MANIFEST)
    args = parser.parse_args()
    check_patch_queue(args.source.resolve(), args.manifest.resolve())
    print(f"rcspp patch queue valid: {args.manifest}")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (OSError, KeyError, ValueError, RuntimeError, json.JSONDecodeError) as exc:
        print(f"rcspp patch queue invalid: {exc}", file=sys.stderr)
        raise SystemExit(1)
