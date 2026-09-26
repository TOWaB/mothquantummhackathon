"""
Dodecahedron faces: 12 source photos (6x 2V0A*, 6x H66A*), each becomes one
face. Each face's subject photo is composited with its pair's photo bled
into the background — winning recipe from set 13/15: distance_gradient
mask (radius=30) on the subject's person-segmentation, strength=0.1,
direction=full.

Pairing is 2V0AxxxxH66Axxxx, arbitrary order (per Bogdan: "no particular
order"). Each pair produces 2 faces (A-as-subject, B-as-subject) = 12 faces
from 6 pairs.

Run with: uv run --python .venv 16_dodecahedron_faces.py
"""
import json
from pathlib import Path

import requests

import atlas
import mask

IMAGES_DIR = Path("images")
OUT_DIR = Path("out/16_dodecahedron_faces")
OUT_DIR.mkdir(parents=True, exist_ok=True)

RADIUS = 30
STRENGTH = 0.1
DIRECTION = "full"

PAIRS = [
    ("2V0A0604mab.jpg", "H66A0009mab.jpg"),
    ("2V0A1228mab.jpg", "H66A1678mab.jpg"),
    ("2V0A6475mab.jpg", "H66A1993mab.jpg"),
    ("2V0A7556mab.jpg", "H66A2008mab.jpg"),
    ("2V0A7693mab.jpg", "H66A2596mab.jpg"),
    ("2V0A8428mab.jpg", "H66A3243mab.jpg"),
]


def build_face(face_num, subject_name, opposite_name):
    print(f"\n--- face {face_num:02d}: subject={subject_name} opposite={opposite_name} ---")

    subject_path = atlas.resize_for_upload(IMAGES_DIR / subject_name, OUT_DIR / f"face{face_num:02d}_subject.png")
    opposite_path = atlas.resize_for_upload(IMAGES_DIR / opposite_name, OUT_DIR / f"face{face_num:02d}_opposite.png")

    alpha = mask.segment_person(subject_path)
    gradient = mask.distance_gradient(alpha, radius=RADIUS)
    mask_path = OUT_DIR / f"face{face_num:02d}_mask.png"
    gradient.save(mask_path)

    subject_asset = atlas.upload_asset(subject_path)
    opposite_asset = atlas.upload_asset(opposite_path)
    mask_asset = atlas.upload_asset(mask_path)

    params = {"strength": STRENGTH, "direction": DIRECTION}
    job_id = atlas.submit_job(
        "telablur-v1", params,
        {"image1": subject_asset, "image2": opposite_asset, "mask": mask_asset},
    )
    st, elapsed = atlas.wait_for_job(job_id)
    print(f"job {job_id}: {st['status']} in {elapsed:.1f}s")

    entry = {
        "face": face_num,
        "subject": subject_name,
        "opposite": opposite_name,
        "params": {**params, "mask_radius": RADIUS, "mask_type": "distance_gradient"},
        "job_id": job_id,
        "status": st["status"],
    }

    if st["status"] != "completed":
        entry["error"] = st.get("error")
        print(f"FAILED: {st.get('error')}")
        return entry

    result = atlas.fetch_result(job_id)
    out_path = OUT_DIR / f"face{face_num:02d}.png"
    for out in result.get("outputs") or []:
        out_path.write_bytes(requests.get(out["url"]).content)
    print(f"saved {out_path}")

    entry["elapsed_s"] = round(elapsed, 1)
    entry["file"] = str(out_path)
    return entry


def main():
    manifest = []
    face_num = 1
    for a, b in PAIRS:
        manifest.append(build_face(face_num, a, b))
        face_num += 1
        manifest.append(build_face(face_num, b, a))
        face_num += 1

    (OUT_DIR / "manifest.json").write_text(json.dumps(manifest, indent=2))
    completed = sum(1 for e in manifest if e["status"] == "completed")
    print(f"\nDone. {completed}/12 faces completed. Manifest: {OUT_DIR / 'manifest.json'}")


if __name__ == "__main__":
    main()
