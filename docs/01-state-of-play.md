# 01. State of play

**As at:** 26 September 2026
**Sources:** `api_log.jsonl` (99 events, 29 jobs), `manifest.json` (12 faces), `served.json`

---

## Measured

### Latency

| Engine | Jobs | Min | p50 | p90 | Max |
|---|---|---|---|---|---|
| `coin-toss-v1` | 27 | 3.5 s | 3.6 s | 3.8 s | 3.9 s |
| `telablur-v1` | 14 | 6.9 s | 7.1 s | 9.6 s | 9.9 s |

Coin toss spreads only 0.4 s across 27 calls, which is consistent with a simulator rather than a queue.

### Cost

| Engine | Credits per job |
|---|---|
| `coin-toss-v1` | 2 |
| `telablur-v1` | 1 |

A spin at eight flips plus one picture is 17 credits, and 16 of them are the flipping.

### Reliability

29 of 29 completed. No errors, no failed status, no retries. `shots` was 1 on every flip.

### One spin

`spin_start` to `spin_face_picked` took 46.1 s and 48.2 s across the two live spins. Two draws each, the first thrown away. Eight flips consumed. The picture job is the fast part at 7.1 s.

---

## The thing that is not settled

Both live spins drew the same eight bits, twelve hours apart.

```
25 Sep 22:09:02   [1,1,1,1] idx 15 rejected   [0,1,1,1] idx 7 accepted   face 8
26 Sep 10:07:38   [1,1,1,1] idx 15 rejected   [0,1,1,1] idx 7 accepted   face 8
```

All 27 `job_id` values are distinct and all 27 `ibm_job_id` values are distinct, so the calls reached the API and were not cached locally.

Across all 27 flips: 20 heads, 7 tails. Under a fair coin, 20 or more heads in 27 has probability 0.0096. Two identical eight-bit prefixes under a fair coin has probability 1/256.

A fixed seed on the `aer` simulator fits the data best. Task A1 settles it.

---

## What exists

| File | State |
|---|---|
| `templates/index.html` | Minimal. `#viewer`, `#credits-bar`, `#stage`, `#spinBtn`, `#status`, `#overlay`, `#log-panel` |
| `static/js/dodeca.js` | The solid. To be replaced, see `03-solid.md` |
| `static/js/app.js` | Spin logic, writes `api_log.jsonl` |
| `out/16_dodecahedron_faces/face01..12.png` | Twelve baked faces, strength 0.1, full, radius 30 |
| Mask pipeline | rembg silhouette, `distance_gradient` radius 30. No `floor` yet |

`served.json` shows side 8 on its third version: original, then reroll, then reblend at strength 0.3, vertical, radius 45.

---

## Unknown

- Credit balance. Caps the size of any overnight pre-generation.
- Concurrency limit. Decides whether a live draw can be 4 s instead of 14 s.
- Whether `shots` above 1 returns per-shot outcomes or only counts.
- Whether `telablur-v1` is deterministic for identical inputs.
- Whether `mask_radius` and `mask_type` are Atlas parameters or our own local record. The `telablur-v1` submit event records only `strength` and `direction`, which suggests the mask is generated locally and uploaded as an asset. If so, the whole mask pipeline is ours with no engine limits on it.

---

## Claims the log currently supports

- Every side was chosen by flips on Atlas, each with a `job_id` and an `ibm_job_id`.
- `backend` is `aer` and `mode` is `emu` on every flip. A simulator.
- 14 picture jobs, 6.9 to 9.9 seconds, zero failures.
- Rejection sampling is visible: a draw over 11 is thrown away and redrawn.

## Claims it does not support

Anything about unpredictability, randomness, or a result being unknown in advance. See A1.
