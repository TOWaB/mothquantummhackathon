# TASKS

**Project:** Quantum Dodecahedron, Moth Hack 2026
**Written:** 26 September 2026
**Exhibition:** Sunday 27 September, 11:00 to 18:00, 19 D'Arblay Street

Every task is sized to run on its own. Each says what done looks like. Nothing here depends on a task further down the list unless it says so.

**Who:** `[Q]` is a quantum decision and belongs to Aja, who should feel free to throw out the suggested approach. `[F]` is frontend. `[B]` is either.

---

## Track A. Measure before building

These answer questions the rest of the build depends on. None takes longer than fifteen minutes of wall time.

- [ ] **A1 `[Q]` Determinism.** `python tools/flip_probe.py 40 > run_a.txt`, restart the shell, run it again into `run_b.txt`, `diff` them. Record whether they match and the heads count across all 80.
  **Done:** a line in `docs/findings.md` saying identical or not, plus heads out of 80.
  **Why it blocks things:** the screen currently claims nothing about unpredictability. This is what unlocks or permanently closes that.

- [ ] **A2 `[B]` Credit balance.** Read the balance, run ten flips, read it again.
  **Done:** credits remaining, and confirmation that a flip costs 2 and a picture costs 1.
  **Blocks:** how many states can be pre-generated overnight.

- [ ] **A3 `[Q]` Does `shots` above 1 return per-shot data?** `python tools/shots_probe.py 8`. Print the whole response object.
  **Done:** the raw response pasted into `docs/findings.md`, and whether it cost 2 credits or 16.
  **Why it matters:** if one job can yield four bits, a draw drops from 14.4 seconds to 3.6.

- [ ] **A4 `[B]` Concurrency.** Submit 4 flips at once, then 8. `python tools/concurrency_probe.py`.
  **Done:** all completed, or the first error code and at what count.

- [ ] **A5 `[B]` Telablur determinism.** Same two assets, same params, three runs, diff the PNGs byte for byte.
  **Done:** identical or not. Decides whether "reroll" produces a different picture at all.

- [ ] **A6 `[Q]` Other entropy engines.** The notes mention `comet-rng`. Pull the catalog and check latency and credit cost against `coin-toss-v1`.
  **Done:** a two-row comparison. If something is cheaper or faster, the whole bit-sourcing design changes.

---

## Track B. The mask

Read `docs/04-mask.md` first. The short version: radius softens the edge, `floor` is what makes the person dissolve, and the current code has no `floor`.

- [ ] **B1 `[B]` Add `floor` and `erode` to the mask generator.** Formula and Python in `docs/04-mask.md`.
  **Done:** `make_mask(sil, radius, erode, floor)` returns an array, and `floor=0` reproduces today's output exactly.

- [ ] **B2 `[Q]` Pick the step size.** Open the mask lab, drag `floor`, run the 200-spin walk at a few step sizes.
  **Done:** one number in `config.yaml`. The suggestion is 0.02 with reflecting bounds. Aja may prefer a different distribution entirely, for instance a step drawn from the flips rather than a fixed size.

- [ ] **B3 `[Q]` Decide where the walk direction comes from.** The suggestion is the discarded draw, which is already paid for and currently thrown away. Alternatives in `docs/02-quantum-open.md`.
  **Done:** a function `walk_step(discarded_bits, accepted_bits) -> float`.

- [ ] **B4 `[B]` Store a `floor` per side.** Twelve numbers in `state/floors.json`, starting at 0, reflecting at 0 and 1.
  **Done:** a spin on side 8 moves side 8's floor and leaves the other eleven alone.

- [ ] **B5 `[B]` Regenerate the mask per spin** so a new version uses the new floor.
  **Done:** two consecutive spins on the same side produce visibly different masks.

---

## Track C. The solid

Read `docs/03-solid.md`. Working code is in there, copy it.

- [ ] **C1 `[F]` Replace `dodeca.js` with the quaternion version.** Whole file in `docs/03-solid.md`.
  **Done:** drag in any direction including diagonal, inertia on release, click a face to bring it round.

- [ ] **C2 `[F]` Check the clip-path nesting.** The transformed element must carry no `clip-path`, `filter`, `opacity` below 1, `mask` or `overflow`. Any of those drops it out of the 3D context and the solid paints flat.
  **Done:** wireframe mode and textured mode show the same shape.

- [ ] **C3 `[F]` Load the real face PNGs** from `out/16_dodecahedron_faces/`.
  **Done:** twelve photographs on the solid, cropped to pentagons, no stand-ins.

- [ ] **C4 `[F]` Snap to the chosen side** when a spin completes. Slerp code is in the doc.
  **Done:** the solid turns the short way round and stops with the chosen face at the camera.

---

## Track D. The screen

Read `docs/05-screen-contract.md`. Every existing id in `index.html` survives.

- [ ] **D0 `[F]` Open `reference/screen.html`.** Static, no JavaScript. Every id matches the contract, every token matches the design doc, every string matches the copy table. Build against it.
  **Done:** you have seen the target.

- [ ] **D1 `[F]` Swap in the new markup.** Additive only, so `app.js` keeps running untouched.
  **Done:** page loads, nothing in the console, old behaviour intact.

- [ ] **D2 `[B]` Add `GET /stream`.** Server-sent events, one event per line written to `api_log.jsonl`, shape unchanged.
  **Done:** `curl -N localhost:5000/stream` prints events during a spin.

- [ ] **D3 `[F]` One `renderEvent(e)` switch** over the seven event types already in the log.
  **Done:** `#log` fills from the stream rather than from a separate code path.

- [ ] **D4 `[F]` The bit ladder.** Driven by `quantum_bit` and `spin_face_picked`. The discarded draw must be visible.
  **Done:** flips land one at a time, and a draw over 11 shows as thrown away.

- [ ] **D5 `[F]` The face panel.** Image first, whole and uncropped, then the settings rows, then the version strip.
  **Done:** clicking a version row loads that version.

- [ ] **D6 `[F]` `POST /spin` returns immediately** with a `spin_id` and does not block.
  **Done:** the browser gets a response in under 100 ms while the job runs.

- [ ] **D7 `[F]` Reset.** Back to the twelve baked faces and zeroed counters.
  **Done:** a judge can watch it run from nothing.

---

## Track E. Copy

Read `docs/06-copy.md`. Two rules: do not explain Moth's platform to Moth, and do not claim a property that has not been tested.

- [ ] **E1 `[B]` Replace every string** from the table in the copy doc.
  **Done:** `grep -ri "random\|unpredict\|nobody knew" templates/ static/` returns nothing.

- [ ] **E3 `[B]` Write the four missing states.** Job failed, credits gone, Atlas unreachable, nothing spun yet. Suggested wording is in `docs/06-copy.md`.
  **Done:** all four render, and none of them shows a stack trace.

- [ ] **E2 `[B]` Revisit after A1.** If the flips turn out not to repeat, unpredictability goes back on the screen with the sample size next to it.

---

## Track F. Ship

- [ ] **F1 `[B]` Repo pushed** with README, the docs folder and the notebook export. Claims Expert 01 and 02.
- [ ] **F2 `[B]` Notebook** from `generate.py`.
- [ ] **F3 `[B]` Record the claims** you can support, with the log lines that support each one.

---

## Cut order if the day runs short

Version strip, then wireframe mode, then the mask drift, then the live `/stream` in favour of a two second poll. The solid, the ladder and the face panel stay.

---

## Documents

| File | What is in it |
|---|---|
| `docs/01-state-of-play.md` | What the log measured, what exists, what is unknown |
| `docs/02-quantum-open.md` | Open decisions for Aja, with options and probe scripts |
| `docs/03-solid.md` | Geometry, the clip-path trap, full quaternion code |
| `docs/04-mask.md` | Mask formula, Python, the drift walk |
| `docs/05-screen-contract.md` | Markup ids, event stream, endpoints |
| `docs/06-copy.md` | Copy rules, the string table, how to write new strings |
| `docs/07-design.md` | Colour, type, spacing, components, states, motion, layout |
| `docs/08-structure.md` | Repo tree, data model, every event and file schema |
| `reference/screen.html` | Static reference screen. Open it beside the build and compare |
| `.claude/skills/quantum-dodeca/SKILL.md` | Project rules for Claude Code |
