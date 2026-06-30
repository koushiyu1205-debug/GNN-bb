#!/usr/bin/env python3
"""Download or print curl lines for lunar south-pole real-map source files."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys
import time

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from lunar_ice_bpc.domain.real_maps import REAL_MAP_REQUIRED_LOLA_LAYERS, real_map_source_catalog


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--raw-map-dir", default="data/raw_maps")
    parser.add_argument("--layers", default="required", help="'required', 'all', or CSV layer keys")
    parser.add_argument("--manifest-output", default="data/manifests/lunar_real_map_download_manifest.json")
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--print-curl", action="store_true")
    parser.add_argument("--probe-only", action="store_true")
    parser.add_argument("--overwrite", action="store_true")
    parser.add_argument("--discard-partial", action="store_true")
    parser.add_argument("--timeout-sec", type=float, default=120.0)
    parser.add_argument("--chunk-size", type=int, default=1024 * 1024)
    args = parser.parse_args()

    raw_map_dir = _project_path(args.raw_map_dir)
    manifest_output = _project_path(args.manifest_output)
    raw_map_dir.mkdir(parents=True, exist_ok=True)
    catalog = real_map_source_catalog(raw_map_dir)
    selected = _select_layers(catalog["layers"], args.layers)
    manifest = {
        "schema_version": "lunar_ice_bpc.real_map_download_manifest.v1",
        "raw_map_dir": str(raw_map_dir),
        "requested_layers": [item["key"] for item in selected],
        "dry_run": bool(args.dry_run),
        "print_curl": bool(args.print_curl),
        "probe_only": bool(args.probe_only),
        "planned_downloads": [_planned_record(item, args.timeout_sec) for item in selected],
        "downloads": [],
    }
    if args.print_curl:
        for item in selected:
            print(_curl_line(item, args.timeout_sec))
    if not args.dry_run:
        try:
            import requests
        except Exception as exc:  # pragma: no cover - exercised only when optional deps are absent.
            manifest["status"] = "REQUESTS_UNAVAILABLE"
            manifest["error"] = f"{type(exc).__name__}: {exc}"
            _write_json(manifest_output, manifest)
            print(f"status: {manifest['status']}")
            print(f"manifest: {manifest_output}")
            return 2
        for item in selected:
            record = _download_one(
                requests=requests,
                item=item,
                overwrite=args.overwrite,
                probe_only=args.probe_only,
                keep_partial=not args.discard_partial,
                timeout_sec=args.timeout_sec,
                chunk_size=args.chunk_size,
            )
            manifest["downloads"].append(record)
            print(f"{record['key']}: {record['status']}")
    manifest["status"] = _manifest_status(manifest["downloads"], dry_run=args.dry_run)
    _write_json(manifest_output, manifest)
    print(f"status: {manifest['status']}")
    print(f"manifest: {manifest_output}")
    return 0 if manifest["status"] in {"DRY_RUN", "PROBE_COMPLETE", "DOWNLOADS_READY", "DOWNLOADS_SKIPPED"} else 1


def _project_path(value: str) -> Path:
    path = Path(value)
    if not path.is_absolute():
        path = ROOT / path
    return path


def _select_layers(layers: list[dict], selector: str) -> list[dict]:
    by_key = {item["key"]: item for item in layers}
    if selector == "required":
        keys = list(REAL_MAP_REQUIRED_LOLA_LAYERS)
    elif selector == "all":
        keys = [item["key"] for item in layers]
    else:
        keys = [part.strip() for part in selector.split(",") if part.strip()]
    missing = [key for key in keys if key not in by_key]
    if missing:
        raise SystemExit(f"unknown layer key(s): {', '.join(missing)}")
    return [by_key[key] for key in keys]


def _planned_record(item: dict, timeout_sec: float) -> dict:
    return {
        "key": item["key"],
        "local_path": item["local_path"],
        "source_url": item["source_url"],
        "source_page": item["source_page"],
        "curl": _curl_line(item, timeout_sec),
    }


def _curl_line(item: dict, timeout_sec: float) -> str:
    timeout = max(1, int(float(timeout_sec)))
    return (
        "curl -L --fail --retry 3 "
        f"--connect-timeout 30 --max-time {timeout} "
        f"-o {item['local_path']} {item['source_url']}"
    )


def _download_one(*, requests, item: dict, overwrite: bool, probe_only: bool, keep_partial: bool, timeout_sec: float, chunk_size: int) -> dict:
    target = Path(item["local_path"])
    if target.exists() and not overwrite:
        return {
            "key": item["key"],
            "status": "already_exists",
            "path": str(target),
            "bytes": target.stat().st_size,
            "source_url": item["source_url"],
        }
    if probe_only:
        return _probe_one(requests=requests, item=item, timeout_sec=timeout_sec)
    tmp = target.with_suffix(target.suffix + ".part")
    started = time.time()
    try:
        with requests.get(item["source_url"], stream=True, timeout=float(timeout_sec)) as response:
            response.raise_for_status()
            tmp.parent.mkdir(parents=True, exist_ok=True)
            total = 0
            with tmp.open("wb") as fh:
                for chunk in response.iter_content(chunk_size=int(chunk_size)):
                    if not chunk:
                        continue
                    fh.write(chunk)
                    total += len(chunk)
            tmp.replace(target)
        return {
            "key": item["key"],
            "status": "downloaded",
            "path": str(target),
            "bytes": target.stat().st_size,
            "elapsed_sec": round(time.time() - started, 3),
            "source_url": item["source_url"],
        }
    except Exception as exc:
        partial_bytes = tmp.stat().st_size if tmp.exists() else 0
        if tmp.exists() and not keep_partial:
            tmp.unlink()
            partial_bytes = 0
        record = {
            "key": item["key"],
            "status": "download_failed",
            "path": str(target),
            "source_url": item["source_url"],
            "error": f"{type(exc).__name__}: {exc}",
            "partial_path": str(tmp),
            "partial_bytes": int(partial_bytes),
        }
        return record


def _probe_one(*, requests, item: dict, timeout_sec: float) -> dict:
    started = time.time()
    try:
        response = requests.get(item["source_url"], stream=True, timeout=float(timeout_sec), headers={"Range": "bytes=0-0"})
        response.raise_for_status()
        size = response.headers.get("Content-Length") or response.headers.get("Content-Range")
        response.close()
        return {
            "key": item["key"],
            "status": "probe_ok",
            "path": item["local_path"],
            "source_url": item["source_url"],
            "source_page": item["source_page"],
            "response_size_header": size,
            "elapsed_sec": round(time.time() - started, 3),
        }
    except Exception as exc:
        return {
            "key": item["key"],
            "status": "probe_failed",
            "path": item["local_path"],
            "source_url": item["source_url"],
            "source_page": item["source_page"],
            "error": f"{type(exc).__name__}: {exc}",
            "elapsed_sec": round(time.time() - started, 3),
        }


def _manifest_status(downloads: list[dict], *, dry_run: bool) -> str:
    if dry_run:
        return "DRY_RUN"
    if not downloads:
        return "DOWNLOADS_SKIPPED"
    if all(item["status"] in {"probe_ok", "probe_failed"} for item in downloads):
        return "PROBE_COMPLETE"
    if all(item["status"] in {"downloaded", "already_exists"} for item in downloads):
        return "DOWNLOADS_READY"
    return "DOWNLOADS_INCOMPLETE"


def _write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")


if __name__ == "__main__":
    raise SystemExit(main())
