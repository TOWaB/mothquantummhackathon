#!/usr/bin/env python3
"""A3. Does shots above 1 return per-shot outcomes, or only counts?

    python tools/shots_probe.py 8

If the response carries an ordered list of outcomes, one job yields four bits and
a draw drops from 14.4s to 3.6s. If it only carries heads/tails counts, that is a
binomial count, which is not uniform and cannot be mapped onto twelve sides.
Also note the credit figure: 2, or 2 per shot?
"""
import sys
import os
import json

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
import atlas

shots = int(sys.argv[1]) if len(sys.argv) > 1 else 8
job_id = atlas.submit_job("coin-toss-v1", {"shots": shots})
st, secs = atlas.wait_for_job(job_id, engine="coin-toss-v1")
result = atlas.fetch_result(job_id)
print(f"job {job_id}  {secs:.1f}s")
print(json.dumps(result, indent=2))
