"""
Recursive chain + person mask combined: does a protected subject survive
5 rounds of background-only accumulation while everything around him drifts?

image1 starts as H66A1993mab.jpg (the horn player). The background mask
computed from that same photo (out/person_mask_background.png, already on
disk) is reused every iteration — the person's position in frame never
changes, so the same mask still protects him after the background has been
replaced. Only the masked (background) region gets teleblurred toward a new
fresh photo each round; strength=0.8 so each state leans mostly toward the
fresh photo (build plan §7's degradation mitigation).

Run with: uv run --python .venv person_mask_recursion.py
"""
import json
from pathlib import Path

import requests

import atlas

IMAGES_DIR = Path("images")
OUT_DIR = Path("out/person_recursion")
OUT_DIR.mkdir(parents=True, exist_ok=True)

ANCHOR_IMAGE = "H66A1993mab.jpg"  # the horn player, protected throughout
MASK_PATH = Path("out/person_mask_background.png")  # white = background, computed earlier
ITERATIONS = 5
STRENGTH = 0.8


def main():
    if not MASK_PATH.exists():
        print(f"{MASK_PATH} not found — run person_mask_test.py first.")
        return

    sources = sorted(IMAGES_DIR.glob("*.jpg")) + sorted(IMAGES_DIR.glob("*.jpeg")) + sorted(IMAGES_DIR.glob("*.png"))
    fresh_sources = [p for p in sources if p.name != ANCHOR_IMAGE]
    if len(fresh_sources) < ITERATIONS:
        print(f"Need {ITERATIONS} non-anchor images, found {len(fresh_sources)}. Will cycle.")

    def next_source(i):
        return fresh_sources[i % len(fresh_sources)]

    print(f"Anchor (protected subject): {ANCHOR_IMAGE}")
    print(f"Mask: {MASK_PATH}")
    print("Uploading mask once, reused every iteration...")
    mask_asset = atlas.upload_asset(MASK_PATH)

    anchor_path = atlas.resize_for_upload(IMAGES_DIR / ANCHOR_IMAGE, OUT_DIR / "state_0.png")

    manifest = []
    prev_asset_id = None
    prev_path = anchor_path

    for n in range(1, ITERATIONS + 1):
        print(f"\n--- state {n} ---")
        image1_asset = prev_asset_id if prev_asset_id else atlas.upload_asset(prev_path)

        fresh_src = next_source(n - 1)
        fresh_resized = atlas.resize_for_upload(fresh_src, OUT_DIR / f"tmp_fresh_{n}.png")
        image2_asset = atlas.upload_asset(fresh_resized)

        params = {"strength": STRENGTH}
        job_id = atlas.submit_job(
            "telablur-v1", params,
            {"image1": image1_asset, "image2": image2_asset, "mask": mask_asset},
        )
        print(f"job {job_id}: image1={'anchor' if n == 1 else f'state_{n-1}'} image2={fresh_src.name}")

        st, elapsed = atlas.wait_for_job(job_id)
        print(f"{st['status']} in {elapsed:.1f}s")

        if st["status"] != "completed":
            print(f"FAILED: {st.get('error')}")
            manifest.append({"state": n, "job_id": job_id, "status": st["status"], "error": st.get("error")})
            break

        result = atlas.fetch_result(job_id)
        out_path = OUT_DIR / f"state_{n}.png"
        for out in result.get("outputs") or []:
            out_path.write_bytes(requests.get(out["url"]).content)
        print(f"saved {out_path}")

        manifest.append({
            "state": n, "job_id": job_id, "engine": "telablur-v1", "params": params,
            "image2_source": fresh_src.name, "elapsed_s": round(elapsed, 1), "file": str(out_path),
        })

        prev_asset_id = atlas.upload_asset(out_path)
        prev_path = out_path

    (OUT_DIR / "manifest.json").write_text(json.dumps(manifest, indent=2))
    print(f"\nDone. {len(manifest)} states in {OUT_DIR}/. Check state_1.png through state_5.png.")


if __name__ == "__main__":
    main()
