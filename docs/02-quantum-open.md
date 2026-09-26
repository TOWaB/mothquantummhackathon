# 02. Open decisions, quantum side

**For:** Aja
**Nothing here is decided.** Each section states the problem, what the log says, and one or more approaches with their trade-offs. Where a suggestion is marked, it is a starting point to argue with, not a plan.

Probe scripts referenced here are in `tools/`. Each is under 60 lines and runs on its own.

---

## Q1. Does `coin-toss-v1` return a fresh sequence?

**What the log says.** Two spins, twelve hours apart, drew the identical eight bits and landed on face 8 both times. Distinct `job_id` and `ibm_job_id` on every call, so the requests did reach the API. Across 27 flips, 20 heads and 7 tails.

**Why it matters.** Everything the screen says about the selection depends on this. Right now the copy claims nothing about unpredictability, on purpose.

**The test.**

```bash
python tools/flip_probe.py 40 > run_a.txt
# close the shell, open a new one
python tools/flip_probe.py 40 > run_b.txt
diff run_a.txt run_b.txt
```

**Three outcomes and what each means.**

| Result | Reading | What changes |
|---|---|---|
| Sequences identical | Seeded simulator | The piece is about a sampling process, not about chance. Copy stays as it is. |
| Sequences differ, heads well above half | Biased source | Debias it, see Q2, and put the debiasing on screen as part of the mechanism |
| Sequences differ, heads near half | The repeat was coincidence | Unpredictability goes back on the screen with the sample size beside it |

None of the three is a bad outcome for the piece. The bad outcome is claiming the third when it is the first.

---

## Q2. If the source is biased, do we debias?

20 heads in 27 is p = 0.0096 under a fair coin. If A1 confirms a real bias, the classic fix is von Neumann:

```python
def von_neumann(bits):
    """Take bits in pairs. 1,0 -> 1. 0,1 -> 0. Discard 1,1 and 0,0.
    Output is unbiased for any fixed p, at the cost of throwing most input away."""
    out = []
    for a, b in zip(bits[0::2], bits[1::2]):
        if a != b:
            out.append(a)
    return out
```

**Trade-off.** At p(heads) = 0.74 the yield is 2·p·(1−p) = 0.385 bits per pair, so about 0.19 output bits per input flip. Four usable bits would cost roughly 21 flips, 42 credits and 75 seconds. That is probably unaffordable at the exhibition and is an argument for the pre-drawn pool in Q4.

**Alternatives worth considering.**
- Leave the bias in and say so. A biased coin still produces a draw nobody chose, and the bias is visible in the counters.
- Debias only the mask-drift bits, where the cost is amortised overnight, and leave the face selection biased.
- Use the bias as the subject. The counter already shows heads and tails; a visible skew is a more interesting fact than a clean one.

Your call. The screen can carry any of these accurately.

---

## Q3. Rejection sampling, or something else

Current approach: four bits give 0 to 15, anything over 11 is thrown away, draw again.

**Why not modulo.** `idx % 12` maps 12, 13, 14, 15 onto 0, 1, 2, 3, so the first four sides come up a third more often than the rest. With twelve sides and a twelve-hour exhibition that skew is visible in the data afterwards.

**Cost of rejection.** Under a fair coin the expected number of draws is 16/12 = 1.33, so 5.33 flips per side. Under the observed heads bias the reject condition is `b0 and b1`, probability 0.74² = 0.548, so expected draws rise to about 2.2 and flips to 8.8. The bias makes rejection roughly 65 percent more expensive.

**Options.**

```python
# A. What exists. Four bits, reject above 11.
def draw_face(flip):
    while True:
        bits = [flip() for _ in range(4)]
        idx = bits[0]*8 + bits[1]*4 + bits[2]*2 + bits[3]
        if idx < 12:
            return idx, bits, False
        # caller records the rejected draw

# B. Keep partial draws. Reject only the bits that caused the failure,
#    rather than all four. Cheaper, harder to explain on screen.

# C. Consume a continuous bit stream from a pool and slide a 4-bit window.
#    Same statistics, no wasted whole draws, works only with a pool.
```

**Worth noting.** The rejection is the best thing on the screen. It is visible evidence of a sampling process and it costs nothing to display. If you make it cheaper, keep it visible.

---

## Q4. Live draws or a pre-drawn pool

A live draw is 46 to 48 seconds, of which 14.4 is API time and the rest is our own sequential gap between submits.

| Approach | Wait | Credits | What it gives up |
|---|---|---|---|
| Live, as now | 48 s | 17 per spin | Nothing, but the queue at the exhibition suffers |
| Live, back-to-back submits | about 16 s | 17 per spin | Nothing. Task A4 tells us if this is safe |
| Live, 4 parallel submits | about 4 s | 17 per spin | Unknown rate limit |
| Pre-drawn pool | instant | same, spent overnight | The flip did not happen while they watched. Screen must say when it did happen |

**Suggestion, to argue with:** both. A pool for throughput, and a "draw it live" button for anyone who wants to watch the full 48 seconds. The pool keeps the real `job_id`, `ibm_job_id` and timestamp per bit, so the provenance is intact, and the screen shows the original time rather than implying it happened just now.

**Pool sizing** depends on the credit balance from A2.

| Faces | Flips, fair coin | Credits | Credits at the observed bias |
|---|---|---|---|
| 100 | 533 | 1,167 | 1,868 |
| 300 | 1,600 | 3,500 | 5,604 |
| 500 | 2,667 | 5,833 | 9,340 |

---

## Q5. Where does the mask drift come from

The mask has a `floor` that decides how much of the effect reaches the middle of the person. See `04-mask.md`. It needs a direction each spin.

**Suggestion:** the discarded draw. Those bits are already paid for and currently thrown away.

```python
def walk_step(discarded_bits, accepted_bits, step=0.02):
    """Direction from the bits we already bought. Falls back to the
    parity of the accepted draw when nothing was discarded."""
    src = discarded_bits if discarded_bits else accepted_bits
    up = sum(src) * 2 > len(src)
    return step if up else -step
```

**Alternatives.** A separate flip, honest but 2 more credits and 3.6 more seconds. A value derived from the `ibm_job_id` hex, free but not a measurement and should not be called one. A fixed alternating pattern, which is not a walk at all.

**Open sub-question:** should the step be fixed, or drawn from the bits so that its size varies too? A variable step gives a heavier-tailed walk and more dramatic jumps. Your call.

---

## Q6. Does `shots` above 1 return per-shot outcomes?

The response object seen so far is `{backend, heads, ibm_job_id, mode, output, shots, tails}` with `shots: 1`.

If `shots: 8` returns eight ordered outcomes, one job gives four bits and a draw drops from 14.4 seconds to 3.6. If it returns only `heads` and `tails` counts, it gives a binomial count, which is **not** uniform and cannot be mapped onto twelve sides without introducing a worse bias than modulo does.

```bash
python tools/shots_probe.py 8
```

Print the whole object. The answer is either a large speedup or nothing.

---

## Q7. Is `coin-toss-v1` even the right engine

The notes list `comet-rng` among the raw-value engines and it has never been called. Worth one catalog read and one call.

If it is cheaper than 2 credits, or faster than 3.6 seconds, or returns more than one bit per job, the whole bit-sourcing design changes and everything above is moot.

```bash
python tools/catalog.py | grep -i -e rng -e coin -e random
```

---

## Q8. Per side or global

The suggestion in `04-mask.md` is a `floor` per side, so the sides people click are the ones that erode and the drift becomes a record of where the room looked.

The alternative is one global floor, so the whole object dissolves together. Simpler, and arguably a stronger statement, but it loses the connection between attention and erosion.

---

## What none of this changes

Whatever you decide, two things hold.

1. Every number that goes on the screen has to be traceable to a line in `api_log.jsonl`.
2. Nothing claims a property that has not been tested. If A1 comes back ambiguous, the screen says less rather than more.
