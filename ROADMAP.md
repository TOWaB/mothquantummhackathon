# ROADMAP

Goals are `TASKS.md` (Tracks A-F). This file tracks status against them, plus anything we changed, merged or added that TASKS.md doesn't say. Update after every step.

---

## Status by track

### Track A. Measure before building — **all six done**
- [x] A1 Determinism — sequences differ, near-fair (36/80 heads). Unpredictability claim now supportable.
- [x] A2 Credit balance — **partially blocked.** No live balance endpoint exists (`/me`, `/me/storage` checked). Per-job cost confirmed from catalog only (coin-toss 2, telablur 1).
- [x] A3 `shots` above 1 — **no.** Aggregate counts only, no per-shot list. No speedup available on this engine.
- [x] A4 Concurrency — **big win.** 4 at once = 7.5s wall, 8 at once = 10.1s wall, zero errors. Recommend switching bit-fetching to concurrent batches.
- [x] A5 Telablur determinism — **yes, deterministic.** Reroll must never reuse a (radius,strength,direction) triple already used on a face, or it silently repeats a past image. Also fixed a real reroll/reblend terminology swap in `06-copy.md` (code was right, doc was backwards).
- [x] A6 / Q7 Other entropy engines — **comet-qrng-v1 tested for real, does not work.** Reversing my earlier flag — see `docs/findings.md`. Stays with `coin-toss-v1`.

All findings in `docs/findings.md`. This closes Track A.

### Track B. The mask — **all five done**
- [x] B1 `floor`/`erode` in mask generator — `mask.make_mask()`. Regression-tested byte-identical to `distance_gradient` at floor=0 (had to keep the old `2*radius` denominator, not the doc's literal `radius` — see finding below).
- [x] B2 Step size — 0.02, the suggested default (matches `08-structure.md`'s `config.yaml` example).
- [x] B3 Walk direction — decision made (not silently): direction from the discarded quantum draw, `floors.walk_step()`. Aja/Bogdan's to override, flagging per the skill's rule 8.
- [x] B4 Per-side floor storage — `state/floors.json` via `floors.py`, reflecting at 0/1.
- [x] B5 Regenerate mask per spin — wired into `app.py`'s `run_spin`: floor steps on every landing (win or repeat), new mask only baked when a regen job actually runs (reroll/reblend), not on a free "original" reveal. Verified directly: floor=0 → deepest interior fully protected (0); floor=0.3 → 76/255, mean abs diff 33.8 across the mask. Real, visible effect.

### Track C. The solid — **all four done**
- [x] C1 Replaced `dodeca.js` with the verbatim quaternion version from `03-solid.md`. Old per-face-matrix3d version retired (it worked, but by luck — no clip-path was in play yet to trigger the trap this version is built to survive).
- [x] C2 Clip-path nesting — the shipped code already puts the transform on `.pface` and `clip-path` on a child `.pclip`, correctly. Added the required `#stage`/`.pface`/`.pclip` CSS from the doc, replacing the old ad hoc rules.
- [x] C3 Real face PNGs load — unchanged wiring, `/api/faces` → `/static/faces/faceNN.png`, `setFaceImage` signature identical between old and new `Dodeca`.
- [x] C4 Snap to chosen side — `dodeca.snapTo(result.face)` replaces the old async `settleOnFace`.

**Verified, not just written:** ran `checkGeometry()` against the actual shipped `dodeca.js` (via a minimal node/DOM stub, not a reimplementation) — 20 corners, 3 faces per corner, `ok: true`. Full HTTP round trip re-tested after the swap: real spin, real job, floor now visible in the response. Server's live at `http://127.0.0.1:5001`.

### Track D. The screen — all done, verified in a real browser
- [x] Backend: `atlas.py` broadcast hook, `GET /stream` (SSE), `versions.py` + `state/versions.json`, `GET /state`, `POST /reset`, `run_spin` error handling (all three branches verified).
- [x] Real gap found and fixed mid-build: every regeneration was overwriting the same face image, destroying version history. Now each version gets its own `faceNN_vN.png` per `08-structure.md`'s own naming convention.
- [x] D0-D1 Frontend: `reference/screen.html`'s markup/CSS lifted into `templates/index.html`/`static/css/style.css`.
- [x] D3-D5 `renderEvent` switch, ladder (rungs land live, one per real flip), face panel + version list, all in `static/js/app.js`.
- [x] D6 Non-blocking `/spin` — confirmed, response is near-instant, all work happens via `/stream` after.
- [x] D7 Reset button wired to `POST /reset` + page reload.

**Verified with a real headless-Chromium run (Playwright + system chromium, not just curl):** page loads clean, `checkGeometry().ok`, a full real spin end to end — rungs land live matching flip count exactly (checked at 2s intervals), the "thrown away"/"counting from zero" dsum text matches `06-copy.md` verbatim, final state renders correctly, face panel and version list populate from real data, log scrolls internally.

**Real bug caught and fixed by actually screenshotting the running page, not just reading the CSS**: `.app{min-height:100%}` (lifted verbatim from the reference) let the log panel push the whole page to 8862px tall instead of scrolling in its own box — `07-design.md`'s own stated trap, which the static reference file never triggered because it never had enough content to expose it. Fixed: `height:100%` + `overflow:hidden`. See `LEARNINGS.md`.

Copy gate (Track E1) run: only matches are the raw Atlas log's technical detail line (`rejected`/`accepted`) and code/CSS syntax (`transform`, `state` as a JS variable) — confirmed these are intentional by checking `reference/screen.html` itself contains the identical "rejected" wording in the same log-panel context. No real violations in visitor-facing prose.

Not yet re-verified live: clicking an older version row when a face has 2+ versions (needs a real repeat-face spin to set up, not run again purely to save credits — the render function was verified directly against real `versions.json` data instead).

### Track E. Copy — all three done
- [x] E1 Replace strings from the table — done as part of the D-track rebuild (`METHOD`, `describe()`, status strings all sourced from `06-copy.md` directly). Grep gate run, no real violations.
- [x] E2 Revisit after A1 — **done.** A1 came back "differs, near half" (80 flips, 45% heads, no repeat) — the "Nothing spun yet"/"Ready" copy already reflects this; no leftover "unpredictable"/"random" claims anywhere.
- [x] E3 Write the four missing states — wired: `job_failed`/`credits`/`unreachable` (backend-triggered, `spin_error` event) + "nothing spun yet" (frontend, `spins===0`). Backend branches verified; frontend rendering of all four not yet exercised live (would need forcing each condition against the real running server, not done to avoid burning credits/time on states nothing has hit in 29+ real jobs so far).

### Track F. Ship
- [ ] F1 Repo pushed
- [ ] F2 Notebook
- [ ] F3 Record claims with supporting log lines

---

## Done already (before this handoff pack existed)

- 12 face images generated (`telablur-v1`, distance-gradient mask, radius 30, strength 0.1, full)
- Flask app, CSS-3D dodecahedron (non-quaternion version, being replaced by C1), live spin, reroll/reblend both tested working
- API/quantum event logging at the source (`atlas.py`/`quantum.py` → `state/api_log.jsonl`)
- `.gitignore` fixed to stop excluding proof data

## Changes / merges made to the handoff pack itself

- Deleted `tools/_atlas.py` (wrong endpoint shape) — probes rewired to the real, working `atlas.py`.
- Merged two drops: `docs/handoff` (original) then `docs/quantum-dodeca-handoff_design` (adds `07-design.md`, `08-structure.md`, `reference/screen.html`, extended `06-copy.md`/`TASKS.md`). Newer versions kept where they differed.
- Found `comet-qrng-v1` in the live catalog — not in any handoff doc. Certified-randomness engine, could replace the whole coin-toss rejection-sampling mechanism. Open decision, same status as the pack's own Q1-Q8 — not decided, flagging here until it's folded into `02-quantum-open.md` or dismissed.
- Repo does not yet match `08-structure.md`'s target layout (`atlas/`, `pipeline/`, `config.yaml`). Not refactored yet — noted, not done.

## Open decisions waiting on Aja/Bogdan

- Q1-Q8 in `docs/02-quantum-open.md`, unchanged.
- Whether to adopt `comet-qrng-v1` instead of / alongside `coin-toss-v1`.
- Whether to do the `08-structure.md` repo refactor before or after the exhibition, given time.

## Interaction fixes (post-feedback round), 2026-09-26

Five items from Bogdan's first real use of the shipped screen, all done and verified with real headless-Chromium clicks (not just code review):

1. **Click a face → shows its picture/data** — real gap (`onFace` was a no-op) plus two real bugs found while fixing it: a pointer-capture conflict that silently swallowed real mouse clicks on the HUD buttons, and a JS temporal-dead-zone crash from removing the idle-timeout gate. All three fixed. Verified: clicking a genuinely-visible non-front face updates the face panel correctly.
2. **A spin lands and stays** — `snapTo()` now sets `autoSpin = false`, so the result face doesn't drift away again after a few seconds. Verified with a real spin, not just a synthetic `snapTo` call.
3. **Reset the photos** — resolved with Bogdan: existing `/reset` already correct (byte-identical to the untouched original bakes), no regeneration needed.
4. **Auto spin start/stop** — `#homeBtn` removed, `#autoSpinBtn` added, toggles a real persistent `autoSpin` flag in `dodeca.js` (not the old always-resumes idle timer). Starts on ("light spin"). Verified: toggling off stops drift, toggling on resumes it.
5. **"Face N" instead of blank/filename** — root cause was worse than "wrong label": version entries never stored `subject`/`opposite` at all (they're face-level constants), so those rows rendered blank. Added `face_pairing` to `GET /state` (derived from `manifest.json`, not invented) and fixed both rows. Verified against the real pairing (face 6 ↔ face 5, matches manifest).

See `LEARNINGS.md` 2026-09-26 for the three real bugs found while implementing this (not just the five asks).

## Mobile optimization, 2026-09-26

Was genuinely broken — confirmed with a real iPhone-viewport screenshot before touching anything: the desktop fix for the log panel (`.app{height:100%;overflow:hidden}`) clipped the entire page on a phone with no way to scroll, so everything past the 3D solid was invisible/cut off.

Fixed via a `@media(max-width:760px)` block: page scrolls naturally on mobile instead of being height-capped, the solid's stage shrinks to a sane size (`52vh`, capped at 340px, was a fixed 320px min-height regardless of screen size), the log gets its own bounded/scrollable box instead of fighting for flex space that no longer exists, and the counters row is condensed slightly.

Verified with real Playwright mobile emulation (`devices['iPhone 13']`), not just reading the CSS: page now scrolls (was impossible before), full screenshots top-to-bottom show every section correctly stacked and readable, and touch-drag genuinely rotates the solid (dispatched real `PointerEvent`s with `pointerType: 'touch'`, matching what an actual touchscreen fires — `dodeca.js` listens to Pointer Events, not touch events directly).

Not yet re-verified on mobile: a full real spin end to end (regression-tested on desktop after the interaction-fixes round; the spin logic itself didn't change here, only CSS, so not re-spending credits to re-prove it works identically on a narrower screen).

## Concurrency guard, 2026-09-26

Real gap: two spins clicked within seconds had zero protection — `served.json`/`floors.json`/`versions.json` are all unlocked read-modify-write, so two concurrent spins landing on the same face could corrupt version numbering, and there was already a dead, unused `_lock` sitting in `app.py` clearly meant for exactly this and never wired up.

Decision: reject the second spin outright (`409`), don't queue. This is one shared object everyone watches live via `/stream`, not a personal-turn system — "someone's already spinning it, watch" is the honest behaviour for a communal exhibition piece, not "you're #2 in line." Also fixes the file-race for free: only one spin thread ever runs at a time server-wide, no per-file locking needed.

Verified for real, not just read: fired two genuinely concurrent `POST /api/spin` requests — one got `200`, the other `409` pointing at the same `spin_id`. A third attempt mid-spin was also rejected. Once the spin completed, a new spin was accepted normally.

## Make the mask visible, 2026-09-26

All of M0-M5 done and verified against the real running app (backend via direct calls/curl, frontend via real headless-Chromium spins — not just code review).

- **M0**: divisor and clamp-vs-lift both confirmed deliberately (real rendered crops), recorded in `docs/findings.md`. Both were already correct in the code; this made that a checked fact instead of an assumption.
- **M1**: a visitor press always rebakes now — the free "first landing shows the untouched original" branch is gone. `served.json`'s `job_ids` tracking (no longer meaningful) dropped too.
- **M2**: `mask_file` on every version entry. Backfill for the 12 overnight faces was a real finding, not the expected work: their masks already existed on disk, byte-identical to a fresh regeneration (checked directly) — the backfill script only copies/records, never re-runs `rembg`.
- **M3**: `spin_mask_ready` event, mask preview + caption + floor readout during the ~7s wait, past-version mask toggle. A real functional constraint surfaced here: the ring overlay can't touch the same file Atlas consumes as masking data, so two files exist per rebake now (a throwaway upload copy, a permanent ring-annotated servable one).
- **M4**: floor column in the version strip.
- **M5**: the 12-cell floor strip under the solid, wired to `floor_stepped` (updates live for everyone, before the job even finishes) and `onFaceSelected` (front-highlight follows drag/click/spin alike).

**Three real bugs found and fixed while verifying this for real, not while reading the code:**
1. A repeat of the earlier TDZ-ordering class of bug (`floorCells`/`floorFills` referenced by a callback that now fires synchronously at construction).
2. Auto-spin drift wasn't stopped for the *duration* of a spin, only at landing — so the ambient rotation silently swapped the face panel to an unrelated random face mid-wait, including hijacking the mask preview. Fixed: `dodeca.setAutoSpin(false)` on `spin_start`.
3. **A spin got stuck for over an hour, live, mid-test** — root cause: zero timeouts anywhere on any `requests` call in `atlas.py` or `app.py`. One stalled network call could silently freeze a spin's background thread forever, and since spins are serialized, that blocks every future spin too, indefinitely, for the rest of the exhibition day. Fixed: a 30s timeout on every HTTP call. This is the most consequential finding of this whole session — checked directly (process/thread state), not assumed.
4. The SSE-drop fallback only ever refreshed counters, so a dropped connection could leave the screen frozen on stale status. Fixed: the fallback now refreshes the whole panel and floor strip too. Root cause of the drop itself unconfirmed (a raw `curl -N` stayed open and correct for 100+s against the same server — looks like a browser/environment quirk, not a server bug).

Full detail on all four in `LEARNINGS.md`, 2026-09-26.
