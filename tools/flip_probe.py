#!/usr/bin/env python3
"""A1. Does coin-toss-v1 return a fresh sequence?

    python tools/flip_probe.py 40 > run_a.txt
    # close the shell, open a new one
    python tools/flip_probe.py 40 > run_b.txt
    diff run_a.txt run_b.txt

Identical files mean the source is seeded. One line per flip so diff is readable.

Uses the repo's real atlas.py client (see LEARNINGS.md, 2026-09-26): the
handoff pack's own tools/_atlas.py guessed an endpoint shape that does not
match the real API and was deleted.
"""
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
import atlas

n = int(sys.argv[1]) if len(sys.argv) > 1 else 40
heads = 0
for i in range(n):
    job_id = atlas.submit_job("coin-toss-v1", {"shots": 1})
    st, secs = atlas.wait_for_job(job_id, engine="coin-toss-v1")
    res = atlas.fetch_result(job_id).get("result", {})
    bit = 1 if res.get("output") == "heads" else 0
    heads += bit
    print(f"{i+1:03d} {bit} {res.get('output')} {secs:.1f}s backend={res.get('backend')} "
          f"mode={res.get('mode')} ibm={res.get('ibm_job_id')}")
print(f"# heads {heads}/{n}", file=sys.stderr)
