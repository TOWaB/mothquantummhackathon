# Findings

## A1. Determinism of `coin-toss-v1` — 2026-09-26

**Test:** `python tools/flip_probe.py 40 > run_a.txt`, then again as a fresh process into `run_b.txt`, diffed.

**Result: sequences differ.** Not one flip in common at any position. All 80 `job_id` and `ibm_job_id` values distinct.

- Run A: 17 heads / 40 (42.5%)
- Run B: 19 heads / 40 (47.5%)
- Combined: 36 heads / 80 (45%) — 0.89 standard deviations below the fair-coin expectation of 40. Not a significant bias.

**Reading, per the three outcomes in `docs/02-quantum-open.md` Q1:** this is outcome 3 — "the repeat was coincidence." The earlier observation (two live spins, 12 hours apart, drawing the identical 8-bit prefix) was a coincidence, not a seeded/deterministic simulator. At n=8 draws, an identical repeat by chance is unlikely (1/256) but not the only explanation, and 80 fresh flips today show no repeat and no meaningful bias.

**What this unblocks:**
- Track E2: unpredictability can go back on the screen, with the sample size next to it (e.g. "80 flips today, no repeat, 45% heads").
- The earlier heads-bias seen in the historical log (20/27, 74%) does not replicate at n=80. Treat that as small-sample noise, not a property of the source.

**What this does not settle:** whether `mode: "emu"` should still be labelled a simulator on screen. Yes — `backend: aer, mode: emu` is Moth's own label, unrelated to whether the sequence repeats. Determinism and "is it a simulator" are two separate claims; A1 only closes the first one.

---

## A2. Credit balance — 2026-09-26

**No live balance endpoint exists.** Checked `GET /me` (identity only: id, email, role) and `GET /me/storage` (storage quota only: upload/output/notebook bytes). Neither carries credits. The only place a balance shows is the `platform.mothquantum.com` web dashboard, which needs a human login — not fetchable with the API key.

**Cost per job, from the live catalog** (`docs/atlas-catalog.json`, `credits_per_run` field): `coin-toss-v1` = 2, `telablur-v1` = 1. This is a flat per-job field on the engine definition, not a function of params — inferred from the schema shape, not verified by watching a real balance move (can't, see above), so treat "flat regardless of `shots`" as likely but unconfirmed.

**Blocks:** pool-size sizing (Q4) can't be computed against a real remaining balance. Bogdan needs to check the dashboard directly if he wants a hard ceiling; otherwise plan against `config.yaml`'s `credit_ceiling` as a self-imposed cap, not a measured one.

---

## A3. Does `shots` above 1 return per-shot outcomes? — 2026-09-26

**No.** `python tools/shots_probe.py 8` → `{"backend": "aer", "heads": 3, "ibm_job_id": "...", "mode": "emu", "output": "tails", "shots": 8, "tails": 5}`. Aggregate counts only, no ordered per-shot list.

**Reading:** the pessimistic branch in Q6. One job cannot yield multiple usable bits from `coin-toss-v1` — a binomial count isn't invertible to independent per-shot bits, and using it that way (e.g. mapping the heads/tails ratio) would reintroduce a real bias, not remove one. The one-job-per-bit design (`shots=1` each) stands as the only sound approach on this engine.

**Consequence:** the draw-time win described in Q6 (14.4s → 3.6s) is not available on `coin-toss-v1`. It may still be available on `comet-qrng-v1` (see A6/Q7) since it batches its own extraction internally rather than exposing raw per-shot data for us to combine — different mechanism, worth checking on its own terms rather than assuming it inherits this same limit.

---

## A4. Concurrency — 2026-09-26

**4 at once: 7.5s wall (not 4 × 3.6s = 14.4s sequential). 8 at once: 10.1s wall (not 28.8s).** All 12 jobs across both batches completed, zero errors, no rate-limit response of any kind.

**This is a bigger win than the pre-drawn pool in Q4.** A draw needs 4 bits; firing all 4 at once takes ~7s instead of ~14s sequential. Worst case with one rejection-redraw (a second batch of 4) is ~14s total, not ~29-50s. This is simpler than a pool (no overnight pre-fetch, no provenance-timestamp-mismatch problem Q4 flagged) and gets most of the same speed win.

**Consequence for Q3/Q4:** recommend switching `quantum_choice`'s bit-fetching from sequential to a 4-wide concurrent batch per draw. Untested above 8 — TASKS.md only asked for 4 then 8, didn't push further, so treat "safe above 8" as unknown, not assumed.

---

## A5. Is telablur-v1 deterministic for identical inputs? — 2026-09-26

**Yes.** Same `image1`, `image2`, `strength`, `direction`, three separate jobs, three separate job ids — byte-identical output all three times (`sha256` first 16 hex: `96b0dedd0c235265`, all three runs, 951,565 bytes each).

**Consequence:** "reroll" only produces a genuinely new picture if it changes at least one param from every previous version of that face — reusing identical params on identical source photos reproduces the exact same file. Our `app.py` already draws fresh `radius`/`strength`/`direction` for every reroll, so this is already handled, but it's now a hard requirement rather than an assumption: **never let reroll reuse a (radius, strength, direction) triple already used on that face.** Not currently checked — 45 possible combinations (5 radii × 3 strengths × 3 directions), a repeat becomes plausible after enough spins on one face over a full exhibition day. Worth a guard, not yet added.

**Found in passing:** `telablur-v1`'s own params (`mask_bin_size`, `mask_min_region`) are separate from our `mask_radius`/`mask_type` bookkeeping fields — confirms `01-state-of-play.md`'s suspicion: the mask really is entirely our own pipeline (rembg + distance_gradient), uploaded as a plain asset. Atlas has its own, different, internal masking knobs we don't touch. `floor`/`erode` (Track B) can go in freely with no engine-side limits.

**Found in passing, a real terminology bug:** `docs/06-copy.md`'s Versions table had `reroll`/`reblend` swapped relative to what the actual code does (checked `app.py` directly). Fixed the table to match the code, not the other way round — the code was already correct and tested; the copy doc's authors had inferred the mapping from a single historical example in `served.json` without reading the source, and guessed backwards.

---

## A6 / Q7. Is `comet-qrng-v1` a better source than `coin-toss-v1`? — 2026-09-26

**Reversing my earlier flag. It is not usable, at least not in `emu` mode, at any parameter size tried.**

Found it in the live catalog (5 credits/run vs `coin-toss-v1`'s 2) — it looked very promising on paper: an SP 800-90B certificate, Toeplitz extraction, CHSH Bell witness, a commit-before-outcome scheme, and a `derive.integers` option that would hand back an already-unbiased 1-12 pick directly, no rejection sampling needed. Ran it for real, three separate parameter sizes (4 qubits/512 shots, 4 qubits/256 shots, 8 qubits/2048 shots): **every one returned `"derivation_error": "no conditioned bytes available"`, `certificate: null`.**

**Why, from the engine's own entropy accounting:** in `emu` mode the backend only returns aggregate `counts`, not ordered per-shot outcomes. Because the extractor can't rule out that shot order carries structure, it subtracts a penalty of `log2(shots!)` bits — at 2048 shots that's **19,580 bits** against a raw budget of only 16,384 bits. The penalty scales faster than the raw budget as shots grow, so more shots make it worse, not better. `budget_bits: 0` every time.

**Reading:** this is the engine being honest, not broken — its own docs say `emu` is "uncertified, simulator-baseline," and this is what that looks like in practice: it doesn't even produce an uncertified value, it produces nothing. Getting real output almost certainly needs `mode: "qpu"` (real per-shot hardware memory readout removes the ordering penalty) — which has the same minutes-to-hours queue problem as `coin-toss-v1`'s `qpu` mode, unusable live.

**Cost of finding this out:** 4 calls × 5 credits = 20 credits, zero usable output. Worth knowing before recommending an engine from its schema alone — a promising `params_schema` is not the same as a working call, and the entropy-accounting fields in the response explain failures the top-level fields don't.

**Verdict on Q7: stays with `coin-toss-v1`.** `comet-qrng-v1` is not a drop-in replacement. Not ruling out `qpu` mode entirely (could be run for the overnight pre-bake, not live), but that's a separate, unexplored question, not a live-spin fix.

---

## M0.1. Mask formula divisor — 2026-09-26

**`mask.py`'s `make_mask` uses `2 × radius`, not the bare `radius` `docs/04-mask.md`'s formula shows.** Deliberate, regression-tested: at `floor=0, erode=0`, `make_mask(alpha, radius=30)` is byte-identical to the pre-existing `distance_gradient(alpha, radius=30)` the twelve baked faces were generated with (confirmed: `np.array_equal` true, max abs diff 0). Using the doc's literal `radius` denominator would have halved the transition width at the same numeric radius and put every already-baked face on a different scale from anything generated after. No rescaling needed — old and new faces are on the same scale.

## M0.2. Clamp vs. lift — 2026-09-26

**Lift**, confirmed by rendering both on a real 200px interior crop (deepest point in face 1's subject silhouette, ~111px from the nearest edge, `floor=0.5`): `docs/crop_clamp.png` (std 7.8 across the crop, visibly flatter/more uniform) vs `docs/crop_lift.png` (std 20.4, visibly retains more of the underlying gradient's shape). Matches the prediction exactly: clamp flattens the interior toward a uniform patch, lift keeps the modelling. `mask.py`'s `make_mask` already implements lift (`floor + (1-floor)*m`) — this confirms it deliberately rather than by assumption.
