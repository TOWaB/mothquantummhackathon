# GOAL: make the mask visible

**Written:** 26 September 2026
**Exhibition:** Sunday 27 September, 11:00 to 18:00

---

## The goal in one sentence

Every time someone changes a side, show them the mask that decided how much of the old picture survived, and show the floor climbing on every side over the course of the day.

---

## Why

Three reasons, in order of how much they matter.

1. **The 7 second telablur wait is currently dead.** The flips are over by then and nothing is on screen. The mask is the one thing that explains itself without a caption.
2. **The mask is ours.** Telablur is Moth's engine. The rembg silhouette, the distance gradient, the floor and the ratchet are the part of the pipeline we built, and in that room it is the part worth showing.
3. **The floor climb is invisible and it is the accumulation argument.** The piece claims the object drifts as people use it. The floor is where that drift actually lives, and right now nobody can see it.

---

## Two things to settle before anything renders

Both change what the preview shows, so they come first.

### 1. Confirm the divisor

Documented in `docs/04-mask.md` as:

```
m = clamp((d + erode) / radius + 0.5, 0, 1)
```

Reported in `LEARNINGS.md` as `(d + erode) / (2 × radius) + 0.5`.

If the code uses `2 × radius`, the transition band is twice as wide as the parameter says, so `radius: 30` produces a 60px feather. That matters because:

- the twelve overnight faces in `manifest.json` were baked at radius 30 under one interpretation, so old and new faces would be on different scales
- the mask lab uses the single-radius slope, so any step size chosen in it is out by a factor of 2

**Read `pipeline/mask.py`. Record which it is in `docs/findings.md`. Do not change it yet.** If the twelve baked faces are on a different scale from what new ones will use, say so and stop, because rescaling twelve faces costs twelve credits and ten minutes and needs to be a decision rather than a side effect.

### 2. Confirm clamp against lift

```python
a = np.clip(m, floor, 1.0)          # plateau: everything below floor flattens
b = floor + (1.0 - floor) * m       # lift: the whole range rises, gradient survives
```

Both produce the same mean shift, so the 33.8 figure in the log cannot tell them apart. They look completely different in the interior of a person: `a` gives a uniform patch with no modelling, `b` keeps the shape.

**Render one 200px interior crop at floor 0.5 under each. Save both. Pick one deliberately.** The rest of the build assumes whichever is chosen and the preview will show it honestly either way.

---

## One upstream fix

`LEARNINGS.md` says a face's floor steps by 0.02 on every landing including `original`, and that `original` does not rebake.

That breaks the claim the interface now makes. The button says **Change a side** and the done state says **it stays that way for whoever comes next**. If a press lands on `original`, nothing changes, the person sees no result, and the claim is false for that press.

**A visitor press always rebakes.** Remove `original` from the method pick on a press. `original` survives only as the label for the twelve faces made in the overnight batch. It is a leftover from the earlier design where a spin might just reveal an existing face, which the button no longer means.

---

## What gets built

Four things, in this order. Each is independently shippable and the first two carry most of the value.

### 1. Mask preview during the rebake

The face panel image slot swaps to the greyscale mask while the telablur job runs, then to the finished picture when it lands.

- One line underneath: **the pale areas are where the new picture comes through**
- The floor number beside it, in violet, mono
- A faint ring on the mask marking the transition zone, since it costs nothing there and is genuinely legible. Not on the photograph.

### 2. Floor in the version strip

`docs/08-structure.md` already specs `floor` on every entry in `versions.json` and the strip already renders those entries. This is a column, not a component.

A side's climb reads down the rows, so a face that has been landed on four times shows four rising numbers.

### 3. A floor strip under the solid

Twelve cells, ink fill on `--track`, side number underneath. One row, full width of the stage, about 14px tall.

**Not gauges on the faces.** At 40 to 90 projected pixels a 12-way gauge is illegible, and `docs/07-design.md` forbids chrome on a photograph. The strip gives the same information, stays readable across the room, and touches nothing.

### 4. The mask saved per version

`face08_v4_mask.png` alongside `face08_v4.png`, and the path stored on the version record. Without this, only the live rebake shows a mask and every past version is unexplainable.

---

## What is deliberately not built

- **Rings drawn on the face texture.** The transition zone is already visible in the photograph as the soft edge. Drawing it again is UI on the artwork.
- **Per-face gauges on the solid.** See above.
- **A floor slider.** The floor is driven by use. A slider makes it a control, which is the opposite of the argument.

---

## Done looks like

- `docs/findings.md` records the divisor and the clamp-against-lift decision, with the two crops saved
- A press always produces a new version
- The mask appears for the 7 seconds the job takes, then the picture
- Every version row shows the floor it was made at
- The strip under the solid climbs over the day
- `state/versions.json` carries `floor` and `mask_file` on every entry
