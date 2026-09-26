#!/usr/bin/env python3
"""A4. How many flips can be in flight at once?

    python tools/concurrency_probe.py

Tries 4, then 8. Stops at the first error and prints the status code, because the
rate limit is undocumented and finding it by accident on Sunday is expensive.
"""
from concurrent.futures import ThreadPoolExecutor
import time
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
import atlas


def one(_):
    t0 = time.time()
    job_id = atlas.submit_job("coin-toss-v1", {"shots": 1})
    st, _ = atlas.wait_for_job(job_id, engine="coin-toss-v1")
    return job_id, st.get("status"), round(time.time() - t0, 2)


for n in (4, 8):
    print(f"\n--- {n} at once ---")
    t0 = time.time()
    try:
        with ThreadPoolExecutor(max_workers=n) as ex:
            for jid, status, secs in ex.map(one, range(n)):
                print(f"  {jid}  {status}  {secs}s")
        print(f"  wall {round(time.time()-t0,2)}s for {n}")
    except Exception as e:
        print(f"  failed at {n}: {type(e).__name__} {e}")
        break
