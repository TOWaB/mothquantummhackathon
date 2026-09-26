#!/usr/bin/env python3
"""A5. Is telablur-v1 deterministic for identical inputs?

    python tools/telablur_determinism.py [image_a] [image_b]

Defaults to two already-uploaded face images if no args given. Three runs,
same params, hashed. Identical hashes mean "reroll" produces the same
picture and only "reblend" changes anything, which the screen copy has to
reflect.
"""
import sys
import os
import hashlib
from pathlib import Path

import requests

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
import atlas

a = Path(sys.argv[1] if len(sys.argv) > 1 else "out/16_dodecahedron_faces/face01_subject.png")
b = Path(sys.argv[2] if len(sys.argv) > 2 else "out/16_dodecahedron_faces/face01_opposite.png")

image1_asset = atlas.upload_asset(a)
image2_asset = atlas.upload_asset(b)

params = {"strength": 0.3, "direction": "vertical"}
hashes = []
for i in range(3):
    job_id = atlas.submit_job("telablur-v1", params, {"image1": image1_asset, "image2": image2_asset})
    st, secs = atlas.wait_for_job(job_id, engine="telablur-v1")
    if st["status"] != "completed":
        print(f"run {i+1} FAILED: {st.get('error')}")
        continue
    result = atlas.fetch_result(job_id)
    url = result["outputs"][0]["url"]
    blob = requests.get(url, timeout=60).content
    h = hashlib.sha256(blob).hexdigest()[:16]
    hashes.append(h)
    print(f"run {i+1}  {job_id}  {secs:.1f}s  {len(blob)} bytes  sha {h}")

print("identical" if len(set(hashes)) == 1 else "different")
