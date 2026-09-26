#!/usr/bin/env python3
"""A6. What else is in the catalog?

    python tools/catalog.py
    python tools/catalog.py | grep -i -e rng -e coin -e random

coin-toss-v1 costs 2 credits and takes 3.6s for one bit. If anything here is
cheaper, faster, or returns more than one bit per job, the whole bit-sourcing
design in 02-quantum-open.md changes.
"""
import json, os, requests
BASE = os.environ.get("MOTH_API_BASE", "https://api.mothquantum.com")
KEY = os.environ["MOTH_API_KEY"]
r = requests.get(f"{BASE}/engines", headers={"Authorization": f"Bearer {KEY}"}, timeout=30)
r.raise_for_status()
data = r.json()
open("docs/atlas-catalog.json", "w").write(json.dumps(data, indent=2))
for e in (data if isinstance(data, list) else data.get("engines", [])):
    print(f"{e.get('id','?'):<22} {str(e.get('credits','?')):<4} {e.get('name','')}")
