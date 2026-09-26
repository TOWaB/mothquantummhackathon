"""
Test set 14: two-layer accumulation with the winning mask config
(distance_gradient radius=30, strength=0.1, direction=full — set 13's best).

anchor = H66A1993mab.jpg. Mask is a fresh gradient built from THIS anchor's
own segmentation (not reused from sets 12/13, which were a different photo).
Same mask reused for both steps, per the original ask ("same mask same
thing").

step 1: state_1 = telablur(anchor, H66A0009mab.jpg, mask)
step 2: state_2 = telablur(state_1, H66A2008mab.jpg, mask)   <- add on top

Run with: uv run --python .venv 14_two_layer_gradient.py
"""
import json
from pathlib import Path

import requests

import atlas
import mask

IMAGES_DIR = Path("images")
OUT_DIR = Path("out/14_two_layer_gradient")
OUT_DIR.mkdir(parents=True, exist_ok=True)

ANCHOR_NAME = "H66A1993mab.jpg"
LAYER1_NAME = "H66A0009mab.jpg"
LAYER2_NAME = "H66A2008mab.jpg"
RADIUS = 30
STRENGTH = 0.1
DIRECTION = "full"


def main():
    print(f"anchor={ANCHOR_NAME}, +{LAYER1_NAME}, +{LAYER2_NAME}")
    anchor_path = atlas.resize_for_upload(IMAGES_DIR / ANCHOR_NAME, OUT_DIR / "state_0.png")

    print("Segmenting anchor, building gradient mask (radius=30)...")
    alpha = mask.segment_person(anchor_path)
    gradient = mask.distance_gradient(alpha, radius=RADIUS)
    mask_path = OUT_DIR / "mask.png"
    gradient.save(mask_path)
    mask_asset = atlas.upload_asset(mask_path)

    params = {"strength": STRENGTH, "direction": DIRECTION}
    manifest = []

    anchor_asset = atlas.upload_asset(anchor_path)
    layer1_path = atlas.resize_for_upload(IMAGES_DIR / LAYER1_NAME, OUT_DIR / "layer1.png")
    layer1_asset = atlas.upload_asset(layer1_path)

    print("\n--- state_1: anchor + layer1 ---")
    job_id = atlas.submit_job(
        "telablur-v1", params,
        {"image1": anchor_asset, "image2": layer1_asset, "mask": mask_asset},
    )
    st, elapsed = atlas.wait_for_job(job_id)
    print(f"job {job_id}: {st['status']} in {elapsed:.1f}s")
    if st["status"] != "completed":
        print(f"FAILED: {st.get('error')}")
        manifest.append({"state": 1, "job_id": job_id, "status": st["status"], "error": st.get("error")})
        (OUT_DIR / "manifest.json").write_text(json.dumps(manifest, indent=2))
        return

    result = atlas.fetch_result(job_id)
    state1_path = OUT_DIR / "state_1.png"
    for out in result.get("outputs") or []:
        state1_path.write_bytes(requests.get(out["url"]).content)
    print(f"saved {state1_path}")
    manifest.append({"state": 1, "job_id": job_id, "params": params,
                      "image2": LAYER1_NAME, "elapsed_s": round(elapsed, 1), "file": str(state1_path)})

    state1_asset = atlas.upload_asset(state1_path)
    layer2_path = atlas.resize_for_upload(IMAGES_DIR / LAYER2_NAME, OUT_DIR / "layer2.png")
    layer2_asset = atlas.upload_asset(layer2_path)

    print("\n--- state_2: state_1 + layer2 (same mask) ---")
    job_id = atlas.submit_job(
        "telablur-v1", params,
        {"image1": state1_asset, "image2": layer2_asset, "mask": mask_asset},
    )
    st, elapsed = atlas.wait_for_job(job_id)
    print(f"job {job_id}: {st['status']} in {elapsed:.1f}s")
    if st["status"] != "completed":
        print(f"FAILED: {st.get('error')}")
        manifest.append({"state": 2, "job_id": job_id, "status": st["status"], "error": st.get("error")})
        (OUT_DIR / "manifest.json").write_text(json.dumps(manifest, indent=2))
        return

    result = atlas.fetch_result(job_id)
    state2_path = OUT_DIR / "state_2.png"
    for out in result.get("outputs") or []:
        state2_path.write_bytes(requests.get(out["url"]).content)
    print(f"saved {state2_path}")
    manifest.append({"state": 2, "job_id": job_id, "params": params,
                      "image2": LAYER2_NAME, "elapsed_s": round(elapsed, 1), "file": str(state2_path)})

    (OUT_DIR / "manifest.json").write_text(json.dumps(manifest, indent=2))
    print(f"\nDone. {len(manifest)} states in {OUT_DIR}/.")


if __name__ == "__main__":
    main()
