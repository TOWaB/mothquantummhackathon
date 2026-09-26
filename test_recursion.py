"""
Recursion test: 5 iterations of the actual chain mechanism, not a one-shot call.

state_1 = telablur(image1=source[0], image2=source[1])
state_N = telablur(image1=state_N-1, image2=source[N])   for N = 2..5

strength=0.8 so each state leans mostly toward the fresh photo with the
previous state at roughly 20% (build plan §7's degradation mitigation):
telablur's own docs give teleblurred_alpha = alpha1*(1-strength) + alpha2*strength,
so strength=0.8 means ~80% image2 (fresh) / ~20% image1 (previous state).

This is also a working prototype of generate.py's core loop and manifest format.
Run with: uv run --python .venv test_recursion.py
"""
import json
import time
from pathlib import Path

import requests

import atlas

IMAGES_DIR = Path("images")
OUT_DIR = Path("out/recursion_test")
OUT_DIR.mkdir(parents=True, exist_ok=True)

ITERATIONS = 5
STRENGTH = 0.8


def download(url: str, dest: Path):
    dest.write_bytes(requests.get(url).content)


def main():
    sources = sorted(IMAGES_DIR.glob("*.jpg")) + sorted(IMAGES_DIR.glob("*.jpeg")) + sorted(IMAGES_DIR.glob("*.png"))
    needed = ITERATIONS + 1
    if len(sources) < needed:
        print(f"Need {needed} images in {IMAGES_DIR}/, found {len(sources)}. Will cycle through what we have.")
    def source(i):
        return sources[i % len(sources)]

    manifest = []
    prev_asset_id = None
    prev_local_path = None

    for n in range(1, ITERATIONS + 1):
        print(f"\n--- state {n} ---")
        if n == 1:
            img1_src = source(0)
            img1_resized = atlas.resize_for_upload(img1_src, OUT_DIR / f"tmp_image1_{n}.png")
            image1_asset = atlas.upload_asset(img1_resized)
        else:
            # previous output is already a PNG at 1024px or smaller; reuse it directly
            image1_asset = prev_asset_id
            img1_src = prev_local_path

        img2_src = source(n)
        img2_resized = atlas.resize_for_upload(img2_src, OUT_DIR / f"tmp_image2_{n}.png")
        image2_asset = atlas.upload_asset(img2_resized)

        params = {"strength": STRENGTH}
        job_id = atlas.submit_job("telablur-v1", params, {"image1": image1_asset, "image2": image2_asset})
        print(f"  job {job_id}: image1={img1_src.name if hasattr(img1_src, 'name') else img1_src} "
              f"image2={img2_src.name} strength={STRENGTH}")

        st, elapsed = atlas.wait_for_job(job_id)
        print(f"  {st['status']} in {elapsed:.1f}s")

        if st["status"] != "completed":
            print(f"  FAILED: {st.get('error')}")
            manifest.append({"state": n, "job_id": job_id, "status": st["status"], "error": st.get("error")})
            break

        result = atlas.fetch_result(job_id)
        out_path = OUT_DIR / f"{n:03d}.png"
        for out in result.get("outputs") or []:
            download(out["url"], out_path)
        print(f"  saved {out_path}")

        manifest.append({
            "state": n,
            "job_id": job_id,
            "engine": "telablur-v1",
            "params": params,
            "image1_source": str(img1_src) if n == 1 else f"state_{n-1}_output",
            "image2_source": img2_src.name,
            "elapsed_s": round(elapsed, 1),
            "file": str(out_path),
        })

        # feed this state's output back in as next iteration's image1
        # (upload the same bytes we just downloaded — no re-encoding needed for the API,
        # but we still register it as a fresh asset since output_asset_id from `result`
        # would also work; this keeps the upload path identical every iteration)
        prev_asset_id = atlas.upload_asset(out_path)
        prev_local_path = out_path

    (OUT_DIR / "manifest.json").write_text(json.dumps(manifest, indent=2))
    print(f"\nDone. {len(manifest)} states written to {OUT_DIR}/, manifest at {OUT_DIR}/manifest.json")
    print("Look at 001.png through 005.png in sequence to judge compounding degradation.")


if __name__ == "__main__":
    main()
