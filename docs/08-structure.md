# 08. Structure

Repo layout, the data model, and the exact shape of every record. Schemas below are read from the real files, not invented.

---

## Tree

```
.
├── app.py                        Flask. Routes, spin orchestration, /stream
├── config.yaml                   MAX_JOBS, credit ceiling, step size, engine slugs
├── atlas/
│   ├── client.py                 submit, poll, upload, download
│   └── engines.py                slug constants, read from the catalog not typed
├── pipeline/
│   ├── mask.py                   rembg -> signed distance -> make_mask
│   ├── generate.py               overnight batch, writes manifest.json
│   └── spin.py                   draw bits -> pick face -> telablur -> new version
├── templates/
│   └── index.html
├── static/
│   ├── js/dodeca.js              the solid, see 03-solid.md
│   ├── js/app.js                 renderEvent, the ladder, the face panel
│   └── css/style.css             Signal tokens, see 07-design.md
├── state/                        mutable, gitignored
│   ├── floors.json               twelve mask floors
│   ├── versions.json             version chain per side
│   └── served.json               what the viewer is currently showing
├── out/
│   └── 16_dodecahedron_faces/    face01.png .. face12.png and later versions
├── docs/                         01 to 08, this pack
├── tools/                        probe scripts
├── api_log.jsonl                 append only, the single source of truth
└── .claude/skills/quantum-dodeca/SKILL.md
```

**Gitignored:** `state/`, `out/`, `api_log.jsonl`, `.env`, `run_*.txt`.
`manifest.json` is committed, because it is the record of the overnight batch.

---

## The one rule about data

`api_log.jsonl` is append only and is the source of truth. Every other state file is a projection of it and can be rebuilt by replaying the log. If a number on screen disagrees with the log, the log is right.

---

## Event schemas

Seven types. Every record has `ts` in ISO 8601 with a timezone, and `type`.

### `spin_start`
```json
{"ts": "2026-09-25T22:08:16.655738+00:00", "type": "spin_start", "spin_id": "e93c1aac"}
```

### `submit`
```json
{"ts": "...", "type": "submit", "engine": "coin-toss-v1",
 "job_id": "3c8e775c-efca-4f26-8764-622fc4c55a2e",
 "params": {"shots": 1}, "credits": 2}
```
`params` carries whatever went to the engine. For `telablur-v1` it has been `{"strength": 0.3, "direction": "vertical"}`. **`mask_radius` and `mask_type` are missing from the submit but present in `manifest.json`**, which is the open question in `01-state-of-play.md`. Whichever way it resolves, log every parameter that affected the output.

### `complete`
```json
{"ts": "...", "type": "complete", "engine": "coin-toss-v1",
 "job_id": "3c8e775c-...", "status": "completed", "elapsed_s": 3.7, "error": null}
```
`elapsed_s` is measured locally, not returned by Atlas. Only `completed` has been seen. Handle failed, cancelled and running without assuming the strings.

### `quantum_bit`
```json
{"ts": "...", "type": "quantum_bit", "job_id": "3c8e775c-...",
 "result": {"backend": "aer", "mode": "emu",
            "ibm_job_id": "23454823045c4569b6ce5e5df7933e0c",
            "heads": 1, "tails": 0, "shots": 1, "output": "heads"}}
```
`result` is the engine response verbatim. Do not reshape it.

### `spin_face_picked`
```json
{"ts": "...", "type": "spin_face_picked", "spin_id": "e93c1aac", "face": 8,
 "bits": [{"bits": [1,1,1,1], "idx": 15, "accepted": false},
          {"bits": [0,1,1,1], "idx": 7,  "accepted": true}]}
```
The whole draw history including discards. This one record drives the ladder.

### `spin_method_pick_start`
```json
{"ts": "...", "type": "spin_method_pick_start", "spin_id": "test01", "face": 8}
```
Fires right before the single quantum_bit() call that decides reroll vs
reblend, so the client can render its ladder rung live rather than
retroactively — same principle as `spin_param_pick_start` below. Unlike
that event and the face pick, this one is always exactly one bit with no
accept/reject branch: heads (bit=1) is reblend, tails (bit=0) is reroll,
both are always valid outcomes.

### `spin_method_picked`
```json
{"ts": "...", "type": "spin_method_picked", "spin_id": "test01", "face": 8, "method": "reroll"}
```
`method` is `original`, `reroll` or `reblend`.

### `spin_param_pick_start`
```json
{"ts": "...", "type": "spin_param_pick_start", "spin_id": "test01", "face": 8,
 "param": "radius", "options": [15, 30, 45, 60, 90]}
```
Fires before each of the three real `quantum_choice()` calls a `reroll`
makes (radius, then strength, then direction, in that order — matching
`RADII`/`STRENGTHS`/`DIRECTIONS` in `app.py`) — live, not retroactive, same
reason as `spin_mask_ready` and `spin_face_picked`'s own live rejection
lines. `options` is that call's full option list, so the client can
compute the same rejection-sampling threshold (`bits_needed`,
`idx < len(options)`) the server already used, and render each real flip
as its own ladder rung as it lands. Does not fire for `reblend`, which
skips all three param picks entirely (see `spin_method_picked`'s handling
in `app.js`).

### `spin_mask_ready`
```json
{"ts": "...", "type": "spin_mask_ready", "spin_id": "03f9d6a5", "face": 11,
 "method": "reblend", "v": 2, "floor": 0.02, "mask_file": "face11_v2_mask.png"}
```
Fires once the mask is built and saved, before the `telablur-v1` job is
submitted — this is what lets the screen show the mask (and its floor) live
during the ~7s render wait, rather than only after `spin_result` lands.
`v` is the version number this spin is about to create. `mask_file` is the
ring-annotated preview under `static/faces/`, not the plain grayscale file
actually uploaded to Atlas (see `docs/mask-tasks` — the ring would corrupt
the real masking data, so two files exist and only this one is ever shown).

### `spin_result`
```json
{"ts": "...", "type": "spin_result", "spin_id": "e93c1aac", "face": 8,
 "method": "original", "job_id": "a92f4af0-...", "elapsed_s": 9.5}
```
`elapsed_s` is absent on `original`, since nothing ran.

---

## File schemas

### `manifest.json`
Array of twelve, the overnight batch.
```json
{"face": 8, "subject": "H66A2008mab.jpg", "opposite": "2V0A7556mab.jpg",
 "params": {"strength": 0.1, "direction": "full",
            "mask_radius": 30, "mask_type": "distance_gradient"},
 "job_id": "a92f4af0-c3da-4f0a-84c3-224730d0c6a3",
 "status": "completed", "elapsed_s": 9.8,
 "file": "out/16_dodecahedron_faces/face08.png"}
```

### `state/versions.json`
The version chain per side. New, derived from `manifest.json` plus every `spin_result`.
```json
{"8": [
  {"v": 1, "method": "original", "job_id": "a92f4af0-...", "elapsed_s": 9.8,
   "params": {"strength": 0.1, "direction": "full", "mask_radius": 30,
              "mask_type": "distance_gradient"},
   "floor": 0.0, "ts": "2026-09-25T19:04:00+00:00",
   "file": "out/16_dodecahedron_faces/face08.png"},
  {"v": 3, "method": "reblend", "job_id": "f32b267e-...", "elapsed_s": 9.6,
   "params": {"strength": 0.3, "direction": "vertical", "mask_radius": 45,
              "mask_type": "distance_gradient"},
   "floor": 0.04, "ts": "2026-09-25T22:12:49+00:00",
   "file": "out/16_dodecahedron_faces/face08_v3.png"}
]}
```
`floor` is new and records the mask floor at the moment that version was made, so the erosion is reconstructable.

### `state/floors.json`
```json
{"1": 0.0, "2": 0.0, "8": 0.04, "12": 0.0}
```
Twelve keys, 0 to 1, reflecting at the bounds. See `04-mask.md`.

### `state/served.json`
What the viewer is showing right now.
```json
{"job_ids": ["a92f4af0-...", "a3177861-...", "f32b267e-..."],
 "current": {"8": {"face": 8, "job_id": "f32b267e-...", "v": 3, "file": "face08_v3.png"}}}
```

---

## Naming

| Thing | Convention | Example |
|---|---|---|
| Face files | `face{NN}.png`, versions `face{NN}_v{N}.png` | `face08_v3.png` |
| Engine slugs | from the catalog, never typed from memory | `coin-toss-v1` |
| Spin ids | 8 hex characters | `e93c1aac` |
| Job ids | whatever Atlas returns, stored whole | full uuid |
| State keys | face number as a string | `"8"` |
| Python | snake_case, modules by pipeline stage | `pipeline/mask.py` |
| JS | camelCase, one file per surface | `renderEvent`, `dodeca.js` |
| CSS | ids for structure, classes for repeated components | `#stage`, `.pface` |

Face numbers are **1 to 12 everywhere on screen and in files**. Bit indices are **0 to 11**. The conversion happens once, at the point the draw is accepted, and the ladder says so out loud: "0 1 1 1 is 7. Counting from zero, that is side 8." Do not let 0-indexing leak anywhere else.

---

## Running it

```bash
python -m venv .venv && source .venv/bin/activate
pip install flask requests numpy scipy pillow rembg pyyaml

cp .env.example .env          # MOTH_API_KEY, MOTH_API_BASE
export $(cat .env | xargs)

python -m pipeline.generate   # overnight, writes manifest.json and out/
flask --app app run --port 5000
```

Probes need only `requests`:
```bash
python tools/flip_probe.py 40 > run_a.txt
```

---

## config.yaml

```yaml
engines:
  coin: coin-toss-v1
  blend: telablur-v1

limits:
  max_jobs: 400          # hard stop, both scripts obey it
  credit_ceiling: 1500   # stop cleanly, do not discover the limit live
  max_concurrency: 1     # raise only after probe A4

mask:
  radius: 30
  erode: 0.0
  floor_step: 0.02       # see 02-quantum-open.md Q5, Aja's call

spin:
  bits_per_draw: 4
  faces: 12
  pool: false            # see 02-quantum-open.md Q4
```

Every number the build depends on lives here, not in the code. When Aja changes a quantum decision it should be one line in this file, not a hunt through `pipeline/`.

---

## Before pushing

```bash
grep -rn "MOTH_API_KEY\s*=\s*['\"]" . --include=*.py --include=*.js   # no hard-coded keys
git check-ignore state out api_log.jsonl                              # all three listed
python -c "import json;[json.loads(l) for l in open('api_log.jsonl')]" # log still parses
grep -rniE "random|unpredict|nobody knew" templates/ static/           # nothing
```
