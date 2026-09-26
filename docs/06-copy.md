# 06. Copy

Two rules, then the strings.

---

## Rule 1. Explain what we built. State what Moth built.

The room on Sunday is Moth's. Anything that explains their platform back to them reads as condescension, and explaining quantum basics to their CSO reads worse.

| Cut | Kept |
|---|---|
| A simulator is a normal computer pretending to be a quantum one | `backend aer · mode emu` |
| Credits are what Moth charges for each job | 2 credits a flip, 1 a picture |
| Moth's receipt for this picture | `job` |
| Asked Moth to flip a coin | `coin-toss-v1 · 3c8e775c · shots 1 · 2 credits` |
| Heads is 1, tails is 0, so 0 0 0 0 is zero | Four flips read as four bits, 0 to 15 |

Fully explained: the piece. Twelve sides, two photographs per side, the rejection, the version chain. Nobody in the room has seen that.

The plain label on each data row stays, with the API field name in small grey underneath. A visitor reads the top line, a judge reads the bottom one. That is labelling a table for a mixed room, not teaching Telablur to Moth.

---

## Rule 2. Never claim a property that has not been tested.

Both logged spins drew the same eight bits twelve hours apart. Until A1 runs, unpredictability is not ours to assert.

| Cannot say | Can say |
|---|---|
| Nobody knew which side you would get | Every side here was chosen by a flip on Atlas, and every flip has a job id |
| Every viewing is unique | This version was made just now and did not exist before the spin |
| The result is random | Four flips make a number from 0 to 15, anything over 11 is thrown away |
| Unpredictable | 8 flips, 16 credits, one go thrown away |

The right column is checkable in `api_log.jsonl`. The left is not checkable at all, and it is vaguer.

---

## The strings

### Persistent

| Where | Copy |
|---|---|
| Title | Quantum Dodecahedron |
| Under the counters | Every side here was chosen by a flip on Atlas, and every flip has a job id. |
| Engine line | Side picked by four `coin-toss-v1` flips, picture from `telablur-v1`. `backend aer · mode emu` |
| Stage tip | Drag to turn. Click a face to bring it round. |
| Panel heads | Facing you · The coin flips · Atlas log |
| Reset | Start again |

### The five states

| State | Line 1 | Line 2 |
|---|---|---|
| Ready | Ready. Press spin. | Four flips pick the side, about 3.6 seconds each. |
| Flipping | Flipping. Flip 2 of 4. | came back heads, 2 credits |
| Thrown away | That is 15. Only 12 sides, so it goes and we draw again. | |
| Picked | Side 8. Mixing the two photos now, about 7 seconds. | 8 flips, 16 credits, one go thrown away. |
| Done | Side 8, version 4. | Picture took 9.2s and cost 1 credit. Job f32b267e. |

Every number in the last two rows comes from the run that just happened.

### The coin flips

| Where | Copy |
|---|---|
| Row | Flip 1 · heads · 1 · job id |
| Discarded | 1 1 1 1 is 15. Only 12 sides, so it goes and we draw again. |
| Accepted | 0 1 1 1 is 7. Counting from zero, that is side 8. |

### Data rows, plain label over API field

| Plain | API |
|---|---|
| Side | `face` |
| First photo | `subject` |
| Second photo | `opposite` |
| How much mixing | `strength` |
| Which way it mixes | `direction` |
| How wide it spreads | `mask_radius` |
| Shape of the mix | `mask_type` |
| Job | `job_id` |
| Took | `elapsed_s` |

### Versions

| API value | On screen |
|---|---|
| `original` | the photograph on its own, nothing mixed in yet |
| `reroll` | run again with new settings, same two photos |
| `reblend` | run again with the same settings, blending onto the last result |

---

## Walk-up script

1. It is a shape with twelve sides. Each side is two photographs from the same concert, mixed into each other.
2. A coin flip on Atlas picks which side you get. Four flips make a number from zero to fifteen, and anything over eleven gets thrown away, because there are only twelve sides.
3. Every side on there has a job id behind it. The flip runs on aer, a simulator, and the screen says so.

If someone asks whether it is random: "Each flip is a separate job on their platform. We have not tested whether the sequence repeats between sessions, so I am not going to claim it does not."

That answer is better than a claim. It is what someone who has read their own logs says.

---

## How to write a string that is not in the table

Six checks, in order. A string that fails any one gets rewritten.

1. **Is it about the piece, or about Moth's platform?** About the piece, explain it. About their platform, state it and stop.
2. **Can the log prove it?** If not, say the thing the log can prove instead.
3. **Is it about the design?** "One number becomes five" and "four fields become nine" describe a change nobody saw. Cut.
4. **Would an eleven year old read it once and understand?** Flip, not measurement. Thrown away, not rejected. Took 9.6 seconds, not elapsed 9.6s.
5. **Does it do exactly one job?** One idea per line. Two ideas are two lines.
6. **Numbers before adjectives.** "27 coin flips", not "a number of measurements".

## Voice

Plain declarative sentences. No em dashes, commas and full stops instead. British English. No exclamation marks. No second person plural, so "we" appears only where a person actually did something, as in "we throw it away and draw again".

Never apologise in an error state and never be vague about what happened. An error says what went wrong and what happens next.

## States with no copy yet

Three gaps. Nothing has failed in 29 jobs, so there is no tested wording for any of these.

| State | Suggested | Why it needs care |
|---|---|---|
| A job fails | "That flip did not come back. Trying again." | Must not imply the piece is broken. Never show a stack trace on a wall. |
| Credits run out | "Out of credits for today. The sides on screen are the ones already made." | Truthful, and the object still works as a viewer |
| Atlas unreachable | "Cannot reach Atlas. Showing the sides made earlier." | The piece must keep running with the baked faces |
| Nobody has spun yet | "Twelve sides, made last night. Press spin to make a thirteenth." | An empty screen is an invitation, not a blank |

Write and test these before Sunday. A failure in front of a judge with no copy for it is worse than the failure.

## Printed wall label

If there is a printed label beside the screen, it carries the walk-up script and nothing else. No QR explanation, no credits, no technical detail. Three sentences, 14pt minimum, ink on white.

## Strings that live in the code, not in a template

`METHOD` in `app.js` maps `original`, `reroll` and `reblend` to their on-screen wording. `describe(ev)` in the event renderer turns each log event into its detail string. Both are copy and both are covered by the rules above. When the table changes, those two objects change with it.

---

## Banned from the screen

random, unpredictable, nobody knew, measurement, amplitude, interference, provenance, instance, state, parameter, rejected, ISA, primitive, quantum-native, leverage, transform.

Plus anything explaining Moth's platform back to Moth: what a simulator is, what credits are, what a job id is.

Check with:

```bash
grep -rniE "random|unpredict|nobody knew|measurement|amplitude|interference" templates/ static/
```

---

## After A1

If the flips turn out not to repeat, unpredictability goes back on the screen with the sample size next to it. If they do repeat, the copy stays exactly as it is and the piece is about a sampling process rather than about chance. That still works.
