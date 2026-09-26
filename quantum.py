"""Genuine quantum randomness for creative decisions, via coin-toss-v1.

Every choice made here (which mask, what strength, which direction) is
decided by a real quantum circuit measurement, not Python's PRNG. Each call
costs 2 credits and ~7s — see docs/atlas-api-docs-reference for the engine.
"""
import math

import atlas


def coin_flip(shots: int = 1) -> dict:
    """One coin-toss-v1 job. Returns {"output": "heads"/"tails", "heads": n, "tails": n, "shots": n}."""
    job_id = atlas.submit_job("coin-toss-v1", {"shots": shots})
    st, _elapsed = atlas.wait_for_job(job_id, engine="coin-toss-v1")
    if st["status"] != "completed":
        raise RuntimeError(f"coin-toss-v1 failed: {st.get('error')}")
    result = atlas.fetch_result(job_id)["result"]
    atlas.log_event({"type": "quantum_bit", "job_id": job_id, "result": result})
    return result


def quantum_bit() -> int:
    """A single fair quantum-measured bit: 1=heads, 0=tails (shots=1)."""
    return 1 if coin_flip(shots=1)["output"] == "heads" else 0


def quantum_bits(n: int) -> list[int]:
    return [quantum_bit() for _ in range(n)]


def quantum_choice(options: list, log: list | None = None):
    """Pick one item from options using quantum bits (rejection-sampled to stay unbiased)."""
    n = len(options)
    if n == 1:
        return options[0]
    bits_needed = max(1, math.ceil(math.log2(n)))
    while True:
        bits = quantum_bits(bits_needed)
        idx = int("".join(map(str, bits)), 2)
        if log is not None:
            log.append({"bits": bits, "idx": idx, "accepted": idx < n})
        if idx < n:
            return options[idx]
