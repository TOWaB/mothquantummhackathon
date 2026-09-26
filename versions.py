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
OUT_DIR = Path("out/16_dodecahedron_faces")
STATIC_FACES = Path("static/faces")


def seed_from_manifest() -> dict:
    faces: dict[str, list] = {}
    if MANIFEST_PATH.exists():
        for entry in json.loads(MANIFEST_PATH.read_text()):
            if entry.get("status") != "completed":
                continue
            n = entry["face"]
            # The baked distance_gradient mask (radius=30, floor=0) that
            # 16_dodecahedron_faces.py already wrote — byte-identical to
            # mask.make_mask(alpha, radius=30, floor=0.0), confirmed in
            # docs/findings.md M0.1. Copied into static/faces here (not just
            # referenced) so it survives a reset the same way every other
            # version's mask does — this used to be a separate one-shot
            # script (17_backfill_v1_masks.py) whose result a reset would
            # silently wipe from versions.json, since seed_from_manifest is
            # exactly what a reset re-runs.
            mask_src = OUT_DIR / f"face{n:02d}_mask.png"
            mask_file = None
            if mask_src.exists():
                mask_file = f"face{n:02d}_v1_mask.png"
                STATIC_FACES.mkdir(parents=True, exist_ok=True)
                (STATIC_FACES / mask_file).write_bytes(mask_src.read_bytes())
            faces.setdefault(str(n), []).append({
                "v": 1,
                "method": "original",
                "job_id": entry["job_id"],
                "elapsed_s": entry.get("elapsed_s"),
                "params": entry["params"],
                "floor": 0.0,
                "ts": None,
                "file": f"face{n:02d}_v1.jpg",
                "mask_file": mask_file,
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
