#!/usr/bin/env python3
"""Create a self-contained runnable capsule for the current P0 V3 control."""

from __future__ import annotations

import argparse
from datetime import datetime, timezone
import gzip
import hashlib
import io
import json
import os
from pathlib import Path
import platform
import stat
import subprocess
import sys
import tarfile
from typing import Iterable


ROOT = Path(__file__).resolve().parents[1]
CAPSULE_ID = "FROZEN_P0V3_FULL_RUNTIME_CAPSULE_20260727"
DEFAULT_OUTPUT = ROOT / "runs" / "frozen_p0v3_full_runtime_capsule_20260727"
ARCHIVE_NAME = "p0v3_full_runtime_capsule.tar.gz"
PROJECT_PREFIX = "GAT_BPC_moonTerk"
FROZEN_BASELINE = (
    ROOT
    / "runs"
    / "frozen_native_live_sri_p0_no_task_wait_baseline_v3_20260725"
)
FROZEN_MODULE_GLOB = "native/lunar_spprc_native*.so"
SMOKE_INSTANCE = (
    ROOT
    / "data"
    / "instances"
    / "lunar_ice_sp50_005"
    / "instance_001_logical_graph.json"
)
EXPECTED_SMOKE_OBJECTIVE = 2.192192


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT)
    args = parser.parse_args()

    output = args.output_dir.resolve()
    require_inside_workspace(output)
    if output.exists() and any(output.iterdir()):
        raise SystemExit(f"refusing to overwrite nonempty capsule: {output}")
    output.mkdir(parents=True, exist_ok=True)

    source_rows = collect_source_rows()
    virtual_rows = collect_virtual_rows()
    content_rows = [
        {
            "path": archive_name(relative),
            "sha256": sha256_bytes(data),
            "size_bytes": len(data),
            "source": str(source.relative_to(ROOT)),
        }
        for relative, source, data in source_rows
    ]
    content_rows.extend(
        {
            "path": archive_name(relative),
            "sha256": sha256_bytes(data),
            "size_bytes": len(data),
            "source": "generated",
        }
        for relative, data in virtual_rows
    )
    content_rows.sort(key=lambda row: row["path"])
    inner_manifest = {
        "schema_version": "lunar_ice_bpc.p0v3_runtime_capsule.v1.inner",
        "capsule_id": CAPSULE_ID,
        "created_at_utc": utc_now(),
        "project_prefix": PROJECT_PREFIX,
        "base_git_commit": git_output("rev-parse", "HEAD"),
        "content_bundle_hash": stable_payload_hash(content_rows),
        "content_file_count": len(content_rows),
        "content_files": content_rows,
        "active_baseline_id": (
            "FROZEN_NATIVE_LIVE_SRI_P0_NO_TASK_WAIT_BASELINE_V3"
        ),
        "runtime_role": (
            "immutable_binary_control_with_compatible_python_shell"
        ),
        "frozen_binary_rebuild_claimed": False,
        "frozen_binary_runtime_replay_required": True,
        "smoke": {
            "instance": archive_name(
                SMOKE_INSTANCE.relative_to(ROOT)
            ),
            "scale": 5,
            "expected_algorithm_status": "BPC_OPTIMAL",
            "expected_exact_status": "BPC_TREE_OPTIMAL",
            "expected_certificate_scope": "BPC_TREE_OPTIMAL",
            "expected_objective": EXPECTED_SMOKE_OBJECTIVE,
            "objective_tolerance": 1.0e-6,
        },
    }
    inner_bytes = canonical_json_bytes(inner_manifest)

    archive = output / ARCHIVE_NAME
    write_deterministic_archive(
        archive,
        source_rows=source_rows,
        virtual_rows=virtual_rows,
        inner_manifest_bytes=inner_bytes,
    )
    frozen_modules = tuple(FROZEN_BASELINE.glob(FROZEN_MODULE_GLOB))
    if len(frozen_modules) != 1:
        raise SystemExit(
            f"expected one frozen native module, found {len(frozen_modules)}"
        )
    outer_manifest = {
        "schema_version": "lunar_ice_bpc.p0v3_runtime_capsule.v1",
        "capsule_id": CAPSULE_ID,
        "created_at_utc": utc_now(),
        "archive": {
            "path": ARCHIVE_NAME,
            "sha256": sha256_file(archive),
            "size_bytes": archive.stat().st_size,
        },
        "content_bundle_hash": inner_manifest["content_bundle_hash"],
        "content_file_count": inner_manifest["content_file_count"],
        "base_git_commit": inner_manifest["base_git_commit"],
        "workspace_status_for_capsule_files": git_status_for_sources(
            source_rows
        ),
        "active_baseline_id": inner_manifest["active_baseline_id"],
        "frozen_native_binary": {
            "path": str(frozen_modules[0].relative_to(ROOT)),
            "sha256": sha256_file(frozen_modules[0]),
            "size_bytes": frozen_modules[0].stat().st_size,
        },
        "smoke": inner_manifest["smoke"],
        "verification": {
            "script": "verify_capsule.py",
            "command": (
                f"{sys.executable} verify_capsule.py --capsule-dir . --smoke"
            ),
        },
        "preservation_boundary": {
            "runtime_replay": True,
            "source_shell_snapshot": True,
            "frozen_native_binary": True,
            "frozen_native_original_rebuild_source": False,
            "reason": (
                "The historical V3 freeze retained the executable module but "
                "not a byte-for-byte copy of every native source file. This "
                "capsule preserves complete runtime use and explicitly does "
                "not claim a reproducible rebuild of that historical binary."
            ),
        },
    }
    atomic_write_json(output / "capsule_manifest.json", outer_manifest)
    verifier_source = ROOT / "scripts" / "verify_p0v3_runtime_capsule.py"
    (output / "verify_capsule.py").write_bytes(verifier_source.read_bytes())
    os.chmod(output / "verify_capsule.py", 0o755)
    (output / "README_ZH.md").write_text(
        render_readme(outer_manifest), encoding="utf-8"
    )
    print(json.dumps(outer_manifest, ensure_ascii=False, indent=2))
    return 0


def collect_source_rows() -> list[tuple[Path, Path, bytes]]:
    mappings: dict[Path, Path] = {}
    for base in (
        ROOT / "src",
        ROOT / "scripts",
        ROOT / "configs",
        ROOT / "native" / "lunar_spprc",
        ROOT / "tests",
        FROZEN_BASELINE,
    ):
        add_tree(mappings, base, base.relative_to(ROOT))
    upstream = ROOT / "build" / "native-spprc" / "_deps" / "rcspp-src"
    add_tree(
        mappings,
        upstream,
        Path("vendor") / "rcspp",
        excluded_names={".git", "__pycache__", ".pytest_cache"},
    )
    for path in (
        ROOT / "README.md",
        ROOT / "pyproject.toml",
        ROOT / "runs" / "native_bpc_baseline_registry.json",
        ROOT
        / "data"
        / "manifests"
        / "lunar_ice_sp50_real_benchmark_manifest.json",
        SMOKE_INSTANCE,
        ROOT / "plan" / "CODEX_HANDOFF_NATIVE_SPPRC_MAINLINE_20260722_ZH.md",
        ROOT / "plan" / "native_live_sri_v1_validity_and_certificate_boundary_zh.md",
    ):
        if not path.is_file():
            raise FileNotFoundError(path)
        mappings[path.resolve()] = path.relative_to(ROOT)
    return [
        (relative, source, source.read_bytes())
        for source, relative in sorted(
            mappings.items(), key=lambda item: str(item[1])
        )
    ]


def collect_virtual_rows() -> list[tuple[Path, bytes]]:
    commands = {
        Path("metadata/python_version.txt"): [
            sys.executable,
            "--version",
        ],
        Path("metadata/pip_freeze.txt"): [
            sys.executable,
            "-m",
            "pip",
            "freeze",
        ],
        Path("metadata/conda_explicit.txt"): [
            str(Path(sys.executable).parents[1] / "bin" / "conda"),
            "list",
            "--explicit",
        ],
    }
    rows: list[tuple[Path, bytes]] = []
    for relative, command in commands.items():
        completed = subprocess.run(
            command,
            cwd=ROOT,
            text=True,
            capture_output=True,
            check=False,
        )
        payload = (
            f"returncode={completed.returncode}\n"
            f"{completed.stdout}{completed.stderr}"
        ).encode("utf-8")
        rows.append((relative, payload))
    frozen_module = next(FROZEN_BASELINE.glob(FROZEN_MODULE_GLOB))
    ldd = subprocess.run(
        ["ldd", str(frozen_module)],
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=False,
    )
    rows.append(
        (
            Path("metadata/frozen_native_ldd.txt"),
            (
                f"returncode={ldd.returncode}\n{ldd.stdout}{ldd.stderr}"
            ).encode("utf-8"),
        )
    )
    rows.append(
        (
            Path("metadata/platform.json"),
            canonical_json_bytes(
                {
                    "python_executable": sys.executable,
                    "python_version": platform.python_version(),
                    "platform": platform.platform(),
                    "machine": platform.machine(),
                }
            ),
        )
    )
    return rows


def add_tree(
    mappings: dict[Path, Path],
    base: Path,
    archive_base: Path,
    *,
    excluded_names: set[str] | None = None,
) -> None:
    excluded = excluded_names or {"__pycache__", ".pytest_cache"}
    if not base.is_dir():
        raise FileNotFoundError(base)
    for path in base.rglob("*"):
        if not path.is_file() or any(part in excluded for part in path.parts):
            continue
        if path.suffix in {".pyc", ".pyo"}:
            continue
        mappings[path.resolve()] = archive_base / path.relative_to(base)


def write_deterministic_archive(
    archive: Path,
    *,
    source_rows: Iterable[tuple[Path, Path, bytes]],
    virtual_rows: Iterable[tuple[Path, bytes]],
    inner_manifest_bytes: bytes,
) -> None:
    members = [
        (archive_name(relative), data, file_mode(source))
        for relative, source, data in source_rows
    ]
    members.extend(
        (archive_name(relative), data, 0o644)
        for relative, data in virtual_rows
    )
    members.append(
        (
            archive_name(Path("metadata") / "capsule_manifest.json"),
            inner_manifest_bytes,
            0o644,
        )
    )
    members.sort(key=lambda row: row[0])
    with archive.open("wb") as raw:
        with gzip.GzipFile(fileobj=raw, mode="wb", mtime=0, filename="") as gz:
            with tarfile.open(fileobj=gz, mode="w", format=tarfile.PAX_FORMAT) as tar:
                for name, data, mode in members:
                    info = tarfile.TarInfo(name=name)
                    info.size = len(data)
                    info.mode = mode
                    info.mtime = 0
                    info.uid = 0
                    info.gid = 0
                    info.uname = ""
                    info.gname = ""
                    tar.addfile(info, io.BytesIO(data))


def archive_name(relative: Path) -> str:
    return str(Path(PROJECT_PREFIX) / relative)


def file_mode(path: Path) -> int:
    mode = stat.S_IMODE(path.stat().st_mode)
    return 0o755 if mode & stat.S_IXUSR else 0o644


def git_status_for_sources(
    rows: Iterable[tuple[Path, Path, bytes]],
) -> str:
    paths = sorted(
        {
            str(source.relative_to(ROOT))
            for _relative, source, _data in rows
            if ROOT in source.parents
        }
    )
    completed = subprocess.run(
        ["git", "-C", str(ROOT.parent), "status", "--short", "--"]
        + [f"{ROOT.name}/{path}" for path in paths],
        text=True,
        capture_output=True,
        check=True,
    )
    return completed.stdout.rstrip()


def render_readme(manifest: dict) -> str:
    smoke = manifest["smoke"]
    return f"""# {CAPSULE_ID}

该目录是P0 V3当前基准的独立可运行保存包。它保留冻结Native二进制、当前
兼容Python运行壳、配置、测试、依赖清单、上游rcspp源码、scale5最小实例
以及80例正式结果快照。

验证并执行最小冷启动复现：

```bash
{manifest['verification']['command']}
```

预期scale5/instance_001得到：

- algorithm status：`{smoke['expected_algorithm_status']}`
- exact status：`{smoke['expected_exact_status']}`
- objective：`{smoke['expected_objective']}`

边界：历史V3冻结没有保存每个Native源码文件的字节副本，因此本包保证
冻结二进制可以完整运行和复现，不宣称能够从源码逐字节重建该历史二进制。
新的large-scale exact pricer必须使用不同backend/engine ID，不能覆盖本目录。
"""


def require_inside_workspace(path: Path) -> None:
    try:
        path.relative_to(ROOT)
    except ValueError as exc:
        raise SystemExit(f"output must be inside workspace: {path}") from exc


def git_output(*args: str) -> str:
    return subprocess.run(
        ["git", "-C", str(ROOT.parent), *args],
        text=True,
        capture_output=True,
        check=True,
    ).stdout.strip()


def canonical_json_bytes(payload: object) -> bytes:
    return (
        json.dumps(
            payload,
            ensure_ascii=False,
            indent=2,
            sort_keys=True,
        )
        + "\n"
    ).encode("utf-8")


def stable_payload_hash(payload: object) -> str:
    return hashlib.sha256(
        json.dumps(
            payload,
            ensure_ascii=True,
            sort_keys=True,
            separators=(",", ":"),
        ).encode("utf-8")
    ).hexdigest()


def sha256_bytes(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def atomic_write_json(path: Path, payload: object) -> None:
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_bytes(canonical_json_bytes(payload))
    os.replace(temporary, path)


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


if __name__ == "__main__":
    raise SystemExit(main())
