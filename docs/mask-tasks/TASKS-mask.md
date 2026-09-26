# TASKS: make the mask visible

Goal and reasoning in `docs/09-goal-mask-visible.md`. Read that first.

`[Q]` is a quantum or mask decision and belongs to Aja. `[F]` is frontend. `[B]` is either.

---

## M0. Settle the maths

Nothing renders until these two are answered. Both are reads and one render, no API calls, no credits.

- [ ] **M0.1 `[Q]` Confirm the divisor.** Read `pipeline/mask.py`. Is it `(d + erode) / radius + 0.5` or `(d + erode) / (2 × radius) + 0.5`?
  **Done:** one line in `docs/findings.md` naming which, plus whether the twelve faces in `manifest.json` were baked under the same one.
  **Stop if:** the twelve baked faces are on a different scale from what new ones will use. Say so and wait. Rescaling twelve faces costs twelve credits and is a decision, not a side effect.

- [ ] **M0.2 `[Q]` Clamp or lift.** Render a 200px interior crop of one silhouette at `floor = 0.5` under both:
  ```python
  a = np.clip(m, floor, 1.0)
  b = floor + (1.0 - floor) * m
  ```
  Save as `docs/crop_clamp.png` and `docs/crop_lift.png`.
  **Done:** both images saved, one chosen, the choice recorded in `docs/findings.md`. Clamp flattens the interior to a uniform patch, lift keeps the modelling. The mean shift is identical for both, so the numbers cannot decide this.

---

## M1. The upstream fix

- [ ] **M1.1 `[B]` A visitor press always rebakes.** Remove `original` from the method pick when the press came from a person. Keep `original` as the label for the twelve overnight faces only.
  **Why:** the button says "Change a side" and the done state says "it stays that way for whoever comes next". A press that lands on `original` makes both false.
  **Done:** ten consecutive presses produce ten new versions. None returns `original`.

- [ ] **M1.2 `[B]` Step the floor only when a rebake happens.** One press, one step, one new version, one mask.
  **Done:** `floors.json` and the version count for a side move together. No silent climb.

---

## M2. Store what the display needs

- [ ] **M2.1 `[B]` Save the mask per version** as `out/16_dodecahedron_faces/face{NN}_v{N}_mask.png`, greyscale, same dimensions as the face.
  **Done:** every new version has a mask file beside it.

- [ ] **M2.2 `[B]` Add `floor` and `mask_file` to every entry in `state/versions.json`.** Schema is already in `docs/08-structure.md`.
  **Done:** a version record carries the floor it was made at and the path to its mask.

- [ ] **M2.3 `[B]` Backfill the twelve overnight faces** with `floor: 0.0` and a regenerated mask file. No API calls needed, the masks are local.
  **Done:** all twelve version-1 records have both fields.

---

## M3. Mask preview during the rebake

- [ ] **M3.1 `[F]` Swap the face panel image to the mask while the job runs.** `#faceimg` src changes to the mask, then to the finished picture on `complete`.
  **Done:** the mask is on screen for the seven seconds the telablur job takes.

- [ ] **M3.2 `[F]` Caption underneath.** One line: `the pale areas are where the new picture comes through`. Style as `.facesub`.
  **Done:** the line appears with the mask and disappears with it.

- [ ] **M3.3 `[F]` Floor number beside the caption.** Violet, mono, 11px. `floor 0.08`.
  **Done:** matches the floor the mask was baked at, not the one after the step.

- [ ] **M3.4 `[F]` Transition ring on the mask.** A faint 1px stroke marking where the gradient crosses 0.5. On the mask only.
  **Done:** visible on the preview, absent from the photograph.

- [ ] **M3.5 `[F]` Past versions show their mask too.** Clicking a version row with a `mask_file` offers the mask as a toggle on the image.
  **Done:** any version made after M2.1 can show its mask.

---

## M4. Floor in the version strip

- [ ] **M4.1 `[F]` Add a floor column to `.vrow`.** Grid becomes `50px 1fr auto auto`. Mono, 9.5px, steel, right aligned above the time.
  **Done:** a side landed on four times shows four rising numbers reading down.

---

## M5. Floor strip under the solid

- [ ] **M5.1 `[F]` Twelve cells under `#stage`.** One row, full width, about 14px tall. Ink fill on `--track`, side number underneath in 9px mono steel. The cell for the side facing you takes the signal fill.
  **Done:** the strip climbs visibly over a session of presses.

- [ ] **M5.2 `[F]` Update on every `spin_result`,** driven by the existing event stream, not a separate fetch.
  **Done:** the strip moves the moment a change lands, including changes made by other people.

**Not built, deliberately:** gauges or rings drawn on the twelve faces of the solid. At 40 to 90 projected pixels they are illegible, and `docs/07-design.md` forbids chrome on a photograph. The strip carries the same information and touches nothing.

---

## Cut order if the day runs short

M5 first, then M3.4, then M3.5, then M4. M0, M1, M2 and M3.1 to M3.3 stay.

---

## Done looks like

- `docs/findings.md` records the divisor and the clamp-against-lift decision, with both crops saved
- Ten presses make ten versions, none of them `original`
- The mask is on screen for the seven seconds the job takes, captioned, with its floor
- Every version row shows the floor it was made at
- The strip under the solid climbs over the day
- `state/versions.json` carries `floor` and `mask_file` on every entry
