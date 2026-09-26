---
name: quantum-dodeca
description: Rules for the Quantum Dodecahedron build for Moth Hack 2026. Use whenever working on this repo, including the Atlas client, coin-toss-v1 and telablur-v1 jobs, the rembg mask pipeline, the CSS 3D dodecahedron in dodeca.js, the Flask viewer, the event log, or any copy that goes on screen. Triggers include atlas, moth, telablur, coin-toss, dodecahedron, face, mask, floor, erode, spin, job_id, ladder, credits, aer.
allowed-tools: Bash(python *) Bash(pip *) Read Write Edit
---

# Quantum Dodecahedron

Twelve pentagon faces, each a Telablur blend of two concert photographs. Four `coin-toss-v1` flips pick which side a visitor gets. Exhibition is Sunday 27 September at 19 D'Arblay Street.

Start at `TASKS.md`. Every task there says what done looks like.

## Measured facts, do not re-derive

- `coin-toss-v1`: 3.5 to 3.9 s, p50 3.6 s, **2 credits**, `shots` 1, `backend aer`, `mode emu`
- `telablur-v1`: 6.9 to 9.9 s, p50 7.1 s, **1 credit**
- 29 of 29 jobs completed, no errors
- One spin is 46 to 48 s from `spin_start` to `spin_face_picked`, mostly our own sequential gap
- **Both logged spins drew the same eight bits twelve hours apart.** Determinism is untested, see `docs/02-quantum-open.md` Q1

## Hard rules

1. **Never claim a property that has not been tested.** No "random", "unpredictable" or "nobody knew" anywhere on screen until the A1 diff comes back clean. Say what the log shows instead: job ids, flip counts, credits, elapsed, discards.
2. **Do not explain Moth's platform to Moth.** The room built it. State `backend aer · mode emu` and move on. No paragraphs about what a simulator is, what credits are, or what a job id is.
3. **Never put `clip-path`, `filter`, `opacity` below 1, `mask` or `overflow` on an element carrying a 3D transform.** It drops out of the 3D rendering context and the solid paints flat. Put them on a child. This has already broken the build once.
4. **Never resubmit a job because a poll failed.** Re-poll the same id. A resubmit spends credits twice.
5. **Never guess an engine slug or a parameter name.** Read `docs/atlas-catalog.json` or stop and ask.
6. **Every number on screen traces to a line in `api_log.jsonl`.** If it cannot be traced, it does not go on screen.
7. **Keep the API key server side.** The browser talks to Flask, never to Atlas.
8. **Do not decide the quantum questions.** `docs/02-quantum-open.md` is Aja's. Implement what is chosen there, offer alternatives, do not pick one and build it silently.

## Geometry, settled

Dodecahedron rings: top 36°, upper 36°, lower 0°, bottom 36°. Inradius `0.6545 × face size`. A pentagon maps onto itself every 72°, so each ring has only two meaningful spins. `Dodeca().checkGeometry()` must return 20 corners with 3 faces at each. Keep that assertion in the shipped code.

## Mask

`m = clamp((d + erode) / radius + 0.5, 0, 1)` then `M = floor + (1 - floor) * m`.

Radius is edge softness and is not a drift parameter. `floor` is what makes the person dissolve. `floor = 0` must reproduce today's output exactly.

## Where things live

| Path | What |
|---|---|
| `TASKS.md` | the task list |
| `docs/01-state-of-play.md` | measured numbers, what is unknown |
| `docs/02-quantum-open.md` | open decisions, Aja's |
| `docs/03-solid.md` | geometry and the whole of `dodeca.js` |
| `docs/04-mask.md` | mask formula and Python |
| `docs/05-screen-contract.md` | markup ids, SSE, endpoints |
| `docs/06-copy.md` | copy rules and the string table |
| `tools/*.py` | probe scripts, each runs on its own |

## Before finishing any screen change

```bash
grep -rniE "random|unpredict|nobody knew|measurement|amplitude|interference" templates/ static/
```

Should return nothing.
