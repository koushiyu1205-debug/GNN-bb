from __future__ import annotations

import importlib.util
import io
import json
from pathlib import Path
import tarfile


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "verify_p0v3_runtime_capsule.py"
SPEC = importlib.util.spec_from_file_location(
    "verify_p0v3_runtime_capsule_for_test", SCRIPT
)
assert SPEC is not None and SPEC.loader is not None
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


def test_archive_audit_rejects_parent_traversal(tmp_path: Path) -> None:
    archive = tmp_path / "unsafe.tar.gz"
    with tarfile.open(archive, mode="w:gz") as handle:
        info = tarfile.TarInfo("../escape")
        payload = b"unsafe"
        info.size = len(payload)
        handle.addfile(info, io.BytesIO(payload))

    _inner, _rows, issues = MODULE.audit_archive(archive)

    assert "unsafe_or_duplicate_member:../escape" in issues
    assert "inner_manifest_missing" in issues


def test_archive_audit_checks_content_hashes(tmp_path: Path) -> None:
    archive = tmp_path / "capsule.tar.gz"
    content_name = "GAT_BPC_moonTerk/example.txt"
    content = b""
    rows = [
        {
            "path": content_name,
            "sha256": MODULE.sha256_bytes(content),
            "size_bytes": len(content),
            "source": "test",
        }
    ]
    inner = {
        "capsule_id": "test",
        "content_files": rows,
        "content_bundle_hash": MODULE.stable_payload_hash(rows),
    }
    with tarfile.open(archive, mode="w:gz") as handle:
        for name, payload in (
            (content_name, content),
            (
                MODULE.INNER_MANIFEST,
                (json.dumps(inner) + "\n").encode(),
            ),
        ):
            info = tarfile.TarInfo(name)
            info.size = len(payload)
            handle.addfile(info, io.BytesIO(payload))

    observed, archive_rows, issues = MODULE.audit_archive(archive)

    assert not issues
    assert observed["capsule_id"] == "test"
    assert set(archive_rows) == {content_name}
