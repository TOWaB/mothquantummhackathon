"""Per-side version history — docs/08-structure.md's state/versions.json.

Mirrors floors.py's convention (flat module, JSON-backed). Seeded from
out/16_dodecahedron_faces/manifest.json (each face's baked "original" is
version 1), then appended to on every visitor press (docs/mask-tasks: a
press always rebakes now, "original" survives only as the seeded v1 label,
never as an outcome of a live press — see LEARNINGS.md 2026-09-26).
"""
import json
from pathlib import Path

VERSIONS_PATH = Path("state/versions.json")
MANIFEST_PATH = Path("out/16_dodecahedron_faces/manifest.json")


def seed_from_manifest() -> dict:
    faces: dict[str, list] = {}
    if MANIFEST_PATH.exists():
        for entry in json.loads(MANIFEST_PATH.read_text()):
            if entry.get("status") != "completed":
                continue
            faces.setdefault(str(entry["face"]), []).append({
                "v": 1,
                "method": "original",
                "job_id": entry["job_id"],
                "elapsed_s": entry.get("elapsed_s"),
                "params": entry["params"],
                "floor": 0.0,
                "ts": None,
                "file": f"face{entry['face']:02d}_v1.jpg",
                "mask_file": None,  # set by 17_backfill_v1_masks.py
            })
    save_versions(faces)
    return faces


def load_versions() -> dict:
    if not VERSIONS_PATH.exists():
        return seed_from_manifest()
    return json.loads(VERSIONS_PATH.read_text())


def save_versions(versions: dict):
    VERSIONS_PATH.parent.mkdir(exist_ok=True)
    VERSIONS_PATH.write_text(json.dumps(versions, indent=2))


def append_version(face: int, method: str, job_id: str, params: dict,
                    elapsed_s: float, floor: float, ts: str, file: str,
                    mask_file: str | None = None) -> dict:
    versions = load_versions()
    key = str(face)
    versions.setdefault(key, [])
    entry = {
        "v": len(versions[key]) + 1,
        "method": method,
        "job_id": job_id,
        "elapsed_s": elapsed_s,
        "params": params,
        "floor": floor,
        "ts": ts,
        "file": file,
        "mask_file": mask_file,
    }
    versions[key].append(entry)
    save_versions(versions)
    return entry


def reset_to_manifest() -> dict:
    return seed_from_manifest()
