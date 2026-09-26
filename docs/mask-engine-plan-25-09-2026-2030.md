# Mask engine plan — from one-off masks to a reusable toolkit

## Problem

Every test script (03, 04, 05, 06, 08, 09) does its own inline rembg call and
saves a raw alpha or its invert. That's why masking currently feels
restrictive:

- No feathering — hard cutout edges only (rembg's matting is soft at the
  pixel level, but the overall region is a fixed binary shape: person or not).
- No erode/dilate — can't grow or shrink the protected region.
- No combining masks — can't union/intersect/subtract two regions.
- No procedural shapes beyond one hardcoded radial gradient (set 03).
- Static across recursion — set 05 reused the exact same mask for all 5
  iterations. The effect can't creep further into the subject over time.
- One segmentation class only — rembg gives "foreground blob," nothing about
  depth, multiple subjects, or partial regions.

## Plan

### Phase 1 — `mask.py` toolkit (do first, cheap, unblocks everything else)

A small module of composable primitives, so every future script imports this
instead of copy-pasting rembg boilerplate:

- `segment_person(image_path) -> Image` — raw alpha matte (wraps rembg)
- `feather(mask, radius) -> Image` — Gaussian blur on the alpha edge
- `erode(mask, px) / dilate(mask, px)` — shrink/grow the region
- `invert(mask)`
- `combine(mask_a, mask_b, op)` — union / intersect / subtract
- `radial_gradient(center, radius, falloff)` — procedural mask (generalizes
  the set-03 pattern mask into a reusable call)
- `lerp(mask_a, mask_b, t)` — blend two masks, for animating a mask across
  a sequence

This directly answers the still-pending soft-edge test from the last plan —
`feather()` is exactly that, just built as a reusable function instead of a
one-off script.

### Phase 2 — iteration-aware masks (the "eat the character" mechanism)

Instead of reusing one static mask every recursion round (set 05's approach),
dilate the mask inward by N px each iteration before the next telablur call.
Round 1 protects the full person; round 5 has crept N×4 px into the
silhouette. This is the concrete way to make the effect progressively consume
the subject rather than stopping at a fixed boundary — directly what was
asked for earlier ("can we... take it anywhere").

### Phase 3 — depth-based masking (optional, bigger lift)

Swap "person vs background" for "near vs far" using a monocular depth model
(e.g. MiDaS). Lets you mask by distance instead of by subject class. Needs a
new model download and more compute per run (~seconds, not blocking) — worth
doing only if the hackathon angle benefits from it; not needed for the
current test sequence.

### Phase 4 — multi-region masks (optional, more complexity, no clear need yet)

Separate mask layers per subject/object, composited with Phase 1's
`combine()`. Skip unless a specific test calls for more than one protected
region.

## Recommended sequence

1. Build `mask.py` (Phase 1) — refactor set 04/09's inline segmentation to
   use it, confirm no regression.
2. Use it to finally run the soft-edge feather test (was pending from the
   last plan).
3. Build the iteration-aware dilate-per-round recursion test (Phase 2) on
   top of the same toolkit.
4. Revisit Phase 3/4 only if there's a specific reason to.

## Status: Phase 1 done, extended with quantum-driven choice (25 Sep, 20:41)

Built `mask.py` (segment/invert/feather/erode/dilate/combine/lerp/
radial_gradient/stripes — all the Phase 1 primitives) and `quantum.py`, which
uses the hackathon's own `coin-toss-v1` engine as the random source instead
of Python's PRNG: each decision (mask recipe, strength, direction) is settled
by real quantum-measured coin flips via `quantum.quantum_choice()`.

`10_quantum_mask_playground.py` ties them together — 8 mask recipes (person,
background, feathered versions of each, a "background_eaten" dilate-into-the-
person variant, radial, and two stripe patterns) x 4 strengths x 3
directions, with the quantum coin picking one combo per run. Ran 6/6 runs
successfully in `out/10_quantum_mask_playground/`; `manifest.json` logs the
raw quantum bits behind every choice, so each run is auditable/reproducible.

This also folds in Phase 2's "eat the character" idea (`on_background_eaten`
recipe = dilate the background mask into the person) as one recipe among
several, rather than a separate script.

Not done yet: Phase 3 (depth-based masking) and Phase 4 (multi-region masks)
— still optional, no clear need yet.
