"""
Test set 15: iteration-aware mask (mask-engine-plan Phase 2). Instead of
reusing one static mask every recursion round (set 05's approach), the
gradient mask dilates further into the person each round — the effect
progressively "eats" the subject instead of stopping at a fixed boundary.

Base mask: distance_gradient(radius=30) from set 13's winning config,
strength=0.1, direction=full. Each round n, the mask is
mask.dilate(base_gradient, px=DILATE_STEP * n) — round 1 barely grows the
base gradient, round 5 has eaten DILATE_STEP*5 px further into the subject.

Run twice:
  - "color": anchor=H66A1993mab.jpg, fresh image each round cycles through
    the other photos (same cycling behaviour as set 05).
  - "bw": anchor=H66A1678mab.jpg, fresh image is H66A2008mab.jpg every round
    (the two b&w images named for this test — only these two, so the same
    fresh image repeats, and only the mask grows between rounds).

Run with: uv run --python .venv 15_iteration_aware_mask.py
"""
import json
from pathlib import Path

import requests

import atlas
import mask

IMAGES_DIR = Path("images")
OUT_ROOT = Path("out/15_iteration_aware_mask")

ITERATIONS = 5
STRENGTH = 0.1
DIRECTION = "full"
RADIUS = 30
DILATE_STEP = 15  # px of additional dilation per round


def run(label, anchor_name, fresh_mode):
    out_dir = OUT_ROOT / label
    out_dir.mkdir(parents=True, exist_ok=True)

    print(f"\n=== [{label}] anchor={anchor_name}, fresh_mode={fresh_mode} ===")
    anchor_path = atlas.resize_for_upload(IMAGES_DIR / anchor_name, out_dir / "state_0.png")

    print("Segmenting anchor, building base gradient mask (radius=30)...")
    alpha = mask.segment_person(anchor_path)
    base_gradient = mask.distance_gradient(alpha, radius=RADIUS)

    if fresh_mode == "cycle":
        sources = sorted(IMAGES_DIR.glob("*.jpg"))
        fresh_sources = [p for p in sources if p.name != anchor_name]
    else:  # fixed
        fresh_sources = [IMAGES_DIR / fresh_mode]

    def next_source(i):
        return fresh_sources[i % len(fresh_sources)]

    manifest = []
    prev_asset = atlas.upload_asset(anchor_path)
    prev_path = anchor_path

    for n in range(1, ITERATIONS + 1):
        dilate_px = DILATE_STEP * n
        print(f"\n--- {label} state {n} (dilate={dilate_px}px) ---")
        current_mask = mask.dilate(base_gradient, px=dilate_px)
        mask_path = out_dir / f"mask_{n}.png"
        current_mask.save(mask_path)
        mask_asset = atlas.upload_asset(mask_path)

        fresh_src = next_source(n - 1)
        fresh_resized = atlas.resize_for_upload(fresh_src, out_dir / f"tmp_fresh_{n}.png")
        fresh_asset = atlas.upload_asset(fresh_resized)

        params = {"strength": STRENGTH, "direction": DIRECTION}
        job_id = atlas.submit_job(
            "telablur-v1", params,
            {"image1": prev_asset, "image2": fresh_asset, "mask": mask_asset},
        )
        print(f"job {job_id}: image1={'anchor' if n == 1 else f'state_{n-1}'} image2={fresh_src.name}")
        st, elapsed = atlas.wait_for_job(job_id)
        print(f"{st['status']} in {elapsed:.1f}s")

        if st["status"] != "completed":
            print(f"FAILED: {st.get('error')}")
            manifest.append({"state": n, "job_id": job_id, "status": st["status"], "error": st.get("error")})
            break

        result = atlas.fetch_result(job_id)
        out_path = out_dir / f"state_{n}.png"
        for out in result.get("outputs") or []:
            out_path.write_bytes(requests.get(out["url"]).content)
        print(f"saved {out_path}")

        manifest.append({
            "state": n, "job_id": job_id, "params": params, "dilate_px": dilate_px,
            "image2_source": fresh_src.name, "elapsed_s": round(elapsed, 1), "file": str(out_path),
        })

        prev_asset = atlas.upload_asset(out_path)
        prev_path = out_path

    (out_dir / "manifest.json").write_text(json.dumps(manifest, indent=2))
    print(f"\n[{label}] done. {len(manifest)} states in {out_dir}/.")


def main():
    run("color", "H66A1993mab.jpg", fresh_mode="cycle")
    run("bw", "H66A1678mab.jpg", fresh_mode="H66A2008mab.jpg")
    print(f"\nAll done. Results in {OUT_ROOT}/color/ and {OUT_ROOT}/bw/.")


if __name__ == "__main__":
    main()
