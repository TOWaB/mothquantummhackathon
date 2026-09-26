"""
Test set 10: let a real quantum coin toss (coin-toss-v1) decide what gets
masked, instead of us picking a recipe/strength/direction by hand.

Every run:
  1. quantum.quantum_choice() burns real quantum-measured bits (coin-toss-v1,
     shots=1 each) to pick a mask recipe, a strength, and a direction.
  2. mask.py builds the chosen mask from a single rembg person segmentation
     of image1 (computed once, reused as the base for every recipe).
  3. telablur-v1 runs with that mask/strength/direction.

This is deliberately wide — 8 mask recipes x 4 strengths x 3 directions —
so we see the range of what "quantum decides the mask" can produce, not one
cherry-picked combo. Costs: ~2 credits per coin flip (several flips/run,
rejection-sampled) + 1 credit per telablur run. Expect ~1-2 min per run.

Run with: uv run --python .venv 10_quantum_mask_playground.py [n_runs]
"""
import json
import sys
from pathlib import Path

import requests

import atlas
import mask
import quantum

IMAGES_DIR = Path("images")
OUT_DIR = Path("out/10_quantum_mask_playground")
OUT_DIR.mkdir(parents=True, exist_ok=True)

IMAGE1_NAME = "H66A1678mab.jpg"  # mask is derived from this one
IMAGE2_NAME = "H66A2008mab.jpg"

STRENGTHS = [0.15, 0.4, 0.65, 0.9]  # 4 = 2 bits, zero rejection waste
DIRECTIONS = ["full", "vertical", "horizontal"]  # 3 = 2 bits, some rejection

N_RUNS = int(sys.argv[1]) if len(sys.argv) > 1 else 6


def build_recipes(person_alpha, size):
    background_alpha = mask.invert(person_alpha)
    return {
        "on_person": lambda: person_alpha,
        "on_background": lambda: background_alpha,
        "on_person_feathered": lambda: mask.feather(person_alpha, radius=15),
        "on_background_feathered": lambda: mask.feather(background_alpha, radius=15),
        "on_background_eaten": lambda: mask.dilate(background_alpha, px=25),
        "radial_from_center": lambda: mask.radial_gradient(size),
        "stripes_vertical": lambda: mask.stripes(size, count=10, direction="vertical"),
        "stripes_horizontal": lambda: mask.stripes(size, count=10, direction="horizontal"),
    }


def main():
    src1 = IMAGES_DIR / IMAGE1_NAME
    src2 = IMAGES_DIR / IMAGE2_NAME
    if not src1.exists() or not src2.exists():
        print(f"Missing source image(s): {src1.exists()=} {src2.exists()=}")
        return

    print(f"image1={IMAGE1_NAME} (mask source), image2={IMAGE2_NAME}")
    image1_path = atlas.resize_for_upload(src1, OUT_DIR / "image1.png")
    image2_path = atlas.resize_for_upload(src2, OUT_DIR / "image2.png")
    image1_asset = atlas.upload_asset(image1_path)
    image2_asset = atlas.upload_asset(image2_path)

    print("Segmenting person out of image1 once (base for every recipe)...")
    from PIL import Image
    size = Image.open(image1_path).size
    person_alpha = mask.segment_person(image1_path)
    recipes = build_recipes(person_alpha, size)
    recipe_names = list(recipes.keys())

    manifest = []
    for i in range(1, N_RUNS + 1):
        print(f"\n=== run {i}/{N_RUNS} — asking the quantum coin ===")
        q_log = {"recipe": [], "strength": [], "direction": []}

        recipe_name = quantum.quantum_choice(recipe_names, log=q_log["recipe"])
        strength = quantum.quantum_choice(STRENGTHS, log=q_log["strength"])
        direction = quantum.quantum_choice(DIRECTIONS, log=q_log["direction"])
        print(f"quantum picked: recipe={recipe_name} strength={strength} direction={direction}")

        run_mask = recipes[recipe_name]()
        mask_path = OUT_DIR / f"run_{i:02d}_mask.png"
        run_mask.save(mask_path)
        mask_asset = atlas.upload_asset(mask_path)

        params = {"strength": strength, "direction": direction}
        job_id = atlas.submit_job(
            "telablur-v1", params,
            {"image1": image1_asset, "image2": image2_asset, "mask": mask_asset},
        )
        st, elapsed = atlas.wait_for_job(job_id)
        print(f"job {job_id}: {st['status']} in {elapsed:.1f}s")

        entry = {
            "run": i, "recipe": recipe_name, "params": params,
            "quantum_log": q_log, "job_id": job_id,
        }
        if st["status"] != "completed":
            print(f"FAILED: {st.get('error')}")
            entry["status"] = st["status"]
            entry["error"] = st.get("error")
            manifest.append(entry)
            continue

        result = atlas.fetch_result(job_id)
        out_path = OUT_DIR / f"run_{i:02d}_result.png"
        for out in result.get("outputs") or []:
            out_path.write_bytes(requests.get(out["url"]).content)
        print(f"saved {out_path}")

        entry["elapsed_s"] = round(elapsed, 1)
        entry["file"] = str(out_path)
        manifest.append(entry)

    (OUT_DIR / "manifest.json").write_text(json.dumps(manifest, indent=2))
    print(f"\nDone. {len(manifest)} quantum-decided runs in {OUT_DIR}/.")


if __name__ == "__main__":
    main()
