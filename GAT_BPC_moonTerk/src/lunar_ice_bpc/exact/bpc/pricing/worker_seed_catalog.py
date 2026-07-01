"""Worker seed catalog updated only by diagnostics."""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class WorkerSeedCatalog:
    rows: list[dict] = field(default_factory=list)

    def record_hidden_negative_audit(self, audit: dict) -> None:
        for row in audit.get("rows", []) or []:
            self.rows.append(
                {
                    "task_set": tuple(str(task_id) for task_id in row.get("hidden_task_set", [])),
                    "path_signature": tuple(tuple(item) for item in row.get("hidden_path_signature", [])),
                    "source": "hidden_negative_audit",
                    "true_reduced_cost": row.get("hidden_true_rc"),
                }
            )

    def to_payload(self) -> dict:
        return {
            "schema_version": "lunar_ice_bpc.b2_worker_seed_catalog.v1",
            "seed_count": len(self.rows),
            "rows": [
                {
                    "task_set": list(row["task_set"]),
                    "path_signature": [list(item) for item in row["path_signature"]],
                    "source": row["source"],
                    "true_reduced_cost": row["true_reduced_cost"],
                }
                for row in self.rows
            ],
            "mutates_certificate": False,
        }

