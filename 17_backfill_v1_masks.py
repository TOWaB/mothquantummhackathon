"""One-shot backfill: give each face's version-1 record its mask_file.

Not a regeneration — out/16_dodecahedron_faces/face{NN}_mask.png already
exists for all 12 faces (written by 16_dodecahedron_faces.py at
distance_gradient(alpha, radius=30), which is byte-identical to
mask.make_mask(alpha, radius=30, floor=0.0) — confirmed directly,
docs/findings.md M0.1). This script only copies those files to the
face{NN}_v1_mask.png convention (permanent + servable copy, matching how
face{NN}_v1.png itself is already handled) and records mask_file on each
face's v==1 entry in state/versions.json. Safe to re-run: skips a face
already backfilled, and only ever touches the v==1 entry, never any
reroll/reblend entry appended since the last reset.

Run with: uv run --python .venv 17_backfill_v1_masks.py
"""
from pathlib import Path

import versions

OUT_DIR = Path("out/16_dodecahedron_faces")
STATIC_FACES = Path("static/faces")


def main():
    STATIC_FACES.mkdir(parents=True, exist_ok=True)
    all_versions = versions.load_versions()
    backfilled = 0
    for face in range(1, 13):
        n = f"{face:02d}"
        src = OUT_DIR / f"face{n}_mask.png"
        if not src.exists():
            print(f"face{n}: no baked mask found, skipping")
            continue

        entries = all_versions.get(str(face), [])
        v1 = next((e for e in entries if e["v"] == 1), None)
        if v1 is None:
            print(f"face{n}: no v1 entry in versions.json, skipping")
            continue
        if v1.get("mask_file"):
            print(f"face{n}: already backfilled ({v1['mask_file']}), skipping")
            continue

        mask_name = f"face{n}_v1_mask.png"
        data = src.read_bytes()
        (OUT_DIR / mask_name).write_bytes(data)
        (STATIC_FACES / mask_name).write_bytes(data)
        v1["mask_file"] = mask_name
        backfilled += 1
        print(f"face{n}: backfilled -> {mask_name}")

    versions.save_versions(all_versions)
    print(f"done. {backfilled} face(s) backfilled.")


if __name__ == "__main__":
    main()
