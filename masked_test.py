"""
Masked-merge test: one real photo + one generated pattern + one generated mask.

Point of this one: prove the *spatial* control works, not just the global
strength blend. image1 = a real photo. image2 = a clean generated pattern
(radial gradient, two colours) — simple on purpose, so the interference is
easy to see against something that isn't already visually busy. mask = a
soft circular vignette: white in the centre, fading to black at the edges.
White = blend happens there. Black = keep the original photo untouched.

Expected result: the middle of the photo should show the quantum interference
with the pattern; the outer frame of the original photo should stay
recognisably itself.

Run with: uv run --python .venv masked_test.py
"""
import json
from pathlib import Path

import numpy as np
import requests
from PIL import Image

import atlas

IMAGES_DIR = Path("images")
OUT_DIR = Path("out")
STATE_DIR = Path("state")
OUT_DIR.mkdir(exist_ok=True)
STATE_DIR.mkdir(exist_ok=True)


def radial_gradient(size, center_color, edge_color):
    """size = (W, H). Smooth radial falloff from center_color to edge_color."""
    w, h = size
    yy, xx = np.mgrid[0:h, 0:w]
    cx, cy = w / 2, h / 2
    dist = np.sqrt((xx - cx) ** 2 + (yy - cy) ** 2)
    max_dist = np.sqrt(cx ** 2 + cy ** 2)
    t = np.clip(dist / max_dist, 0, 1)[..., None]  # 0 at center, 1 at edge
    center = np.array(center_color, dtype=np.float64)
    edge = np.array(edge_color, dtype=np.float64)
    rgb = (center * (1 - t) + edge * t).astype(np.uint8)
    return Image.fromarray(rgb, "RGB")


def radial_mask(size):
    """White (255) at center, black (0) at edges — same falloff shape."""
    w, h = size
    yy, xx = np.mgrid[0:h, 0:w]
    cx, cy = w / 2, h / 2
    dist = np.sqrt((xx - cx) ** 2 + (yy - cy) ** 2)
    max_dist = np.sqrt(cx ** 2 + cy ** 2)
    t = np.clip(dist / max_dist, 0, 1)
    gray = ((1 - t) * 255).astype(np.uint8)
    return Image.fromarray(gray, "L")


def main():
    sources = sorted(IMAGES_DIR.glob("*.jpg")) + sorted(IMAGES_DIR.glob("*.jpeg")) + sorted(IMAGES_DIR.glob("*.png"))
    if not sources:
        print(f"No images found in {IMAGES_DIR}/.")
        return
    src = sources[0]
    print(f"Base photo: {src.name}")

    photo_path = atlas.resize_for_upload(src, OUT_DIR / "masked_test_photo.png")
    w, h = Image.open(photo_path).size
    print(f"Working size: {w}x{h}")

    pattern = radial_gradient((w, h), center_color=(30, 20, 90), edge_color=(240, 180, 60))
    pattern_path = OUT_DIR / "masked_test_pattern.png"
    pattern.save(pattern_path)
    print(f"Generated pattern: {pattern_path}")

    mask = radial_mask((w, h))
    mask_path = OUT_DIR / "masked_test_mask.png"
    mask.save(mask_path)
    print(f"Generated mask: {mask_path}")

    print("Uploading photo (image1)...")
    image1_asset = atlas.upload_asset(photo_path)
    print("Uploading pattern (image2)...")
    image2_asset = atlas.upload_asset(pattern_path)
    print("Uploading mask...")
    mask_asset = atlas.upload_asset(mask_path)

    params = {"strength": 0.6}
    job_id = atlas.submit_job(
        "telablur-v1", params,
        {"image1": image1_asset, "image2": image2_asset, "mask": mask_asset},
    )
    print(f"Submitted job {job_id}")

    print("Polling...", end="", flush=True)
    st, elapsed = atlas.wait_for_job(job_id)
    print(f"\nDone in {elapsed:.1f}s, status={st['status']}")

    if st["status"] != "completed":
        print(f"Job failed: {st.get('error')}")
        return

    result = atlas.fetch_result(job_id)
    out_path = OUT_DIR / f"masked_test_{job_id}_result.png"
    for out in result.get("outputs") or []:
        data = requests.get(out["url"]).content
        out_path.write_bytes(data)
        print(f"Saved {out_path} ({len(data)} bytes)")

    log = {
        "job_id": job_id,
        "engine": "telablur-v1",
        "params": params,
        "image1": src.name,
        "image2": "generated radial gradient",
        "mask": "generated radial vignette (white center, black edge)",
        "elapsed_s": round(elapsed, 1),
        "output_file": str(out_path),
    }
    (STATE_DIR / f"masked_test_{job_id}.json").write_text(json.dumps(log, indent=2))
    print(f"\nLogged to state/masked_test_{job_id}.json")


if __name__ == "__main__":
    main()
