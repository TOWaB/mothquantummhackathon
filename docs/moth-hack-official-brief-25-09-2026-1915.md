# Moth Hack 2026: official brief (from the hackathon repo)

**Source:** github.com/moth-quantum/moth-hack-sep-2026, `content/event.ts` — Moth's
own words, marked in the source as "Single source of truth for everything the
page says" and "Official copy (approved 4 Sept): keep verbatim." Live site:
hack.mothquantum.com. Pulled 25 September 2026, 19:15.

This supersedes anything in `moth-hack-build-plan-25-09-2026-1832.md` or the
research brief where they disagree — those were written from third-party
inference before this repo was checked directly.

---

## 1. What changed vs our working plan

- **Prize amounts are now public:** £100 per Beginner challenge, £150 per
  Intermediate, £200 per Expert. Our build plan claims 8 of 10 challenges —
  at these rates that's £100×3 + £150×3 + £200×2 = £1,750 if every claim holds up.
- **The virtual hackathon window is longer than "Saturday only."** It runs
  26 Sept to 2 Oct, worldwide. The in-person pop-up is just Sat 26 / Sun 27 Sept
  at the Soho venue. Winners announced Mon 5 Oct on Discord.
- **There's a Friday opening event** (17:30–22:00, 25 Sept — tonight) we hadn't
  accounted for, with its own Luma RSVP link.
- **Challenges are numbered 1–10 across all three tiers**, not per-tier
  Beginner-01/Intermediate-01 style. Numbering below matches the source exactly.
- **Submission is still pending.** The `submit` link has `href: null` in the
  source — the button renders disabled with label "Submit project" until Moth
  turns it on. Don't expect a live submission URL yet.
- **Venue postcode has a live TBC:** the source code itself flags
  "W1F 8ED" with `// TBC: confirm 8ED vs 8EF."` Don't print the postcode
  anywhere final without checking Discord first.

## 2. Schedule

| When | What |
|---|---|
| Fri 25 Sept, 17:30–22:00 | Moth Hack opening (tonight) |
| Sat 26 Sept, 10:00–18:00 | Hack Popup Day 01 (in-person, Soho) |
| Sun 27 Sept, 11:00–17:00 | Hack Popup Day 02 (in-person, Soho) |
| 26 Sept – 2 Oct | Virtual hackathon, worldwide |
| Mon 5 Oct | Winners announced, on Discord |

Note the in-person hours differ slightly from what we had (10:00–18:00 Sat,
11:00–17:00 Sun, not 10:00–19:00 / 11:00–18:00).

### Venue

19 D'Arblay Street, Soho, London W1F 8ED (postcode last digit unconfirmed —
see above). Maps link: maps.google.com/?q=19+D'Arblay+Street+London+W1F+8ED

### Saturday 26 Sept agenda (in-person, Moth team talks)

| Time | Who | Talk |
|---|---|---|
| 10:00 | — | Space opens to the public |
| 10:30 | Harry | Welcome, introducing Moth |
| 11:00 | Natasha | Quantum games and an introduction to the Quantum Game Jam |
| 11:30 | James | What is quantum computing? (incl. proc-gen quantum games) |
| 12:00 | Spencer | Introducing Atlas — the web app and API, today's schedule, how to submit |
| 12:30 | Daniel | Deep dive on the Tessa Image engine |
| 14:00 | João | Engines deep dive: Blur and Entanglement Shader |
| 14:30 | Declan | Vibecoding apps for new creative practices |
| 15:30 | Stewart | Quantum computing fundamentals for non-experts |
| 16:00 | Spencer | Deep dive on Quantum Backrooms |
| 18:00 | Harry + team | End of day wrap-up |
| 19:00 | — | Beers and pizza (London hack members) |

**Spencer's noon talk is the one that matters most for us** — it's the live
introduction to the Atlas API and submission process, the exact unknowns our
research brief flagged as gated behind onboarding/Discord.

### Sunday 27 Sept agenda

| Time | Who | Talk |
|---|---|---|
| 10:00 | — | Space opens to the public |
| 10:30 | Harry + team | Welcome back, recap, today's schedule |
| 11:00 | Spencer | Atlas recap, reminder on submitting projects |
| 14:00 | Harry | Post-lunch hackathon updates |
| 14:30 | Declan | Vibecoding apps (different app walkthrough) |
| 18:00 | Harry | End of day wrap-up, space closes |

## 3. Challenges (verbatim from Moth)

### Beginner — £100 prize per challenge

| # | Title | Brief |
|---|---|---|
| 1 | One image, one engine | Run an image through a visual engine (Blur, Tessa, or another) and submit the result with the parameters used. |
| 2 | Make it audible | Use an Atlas engine for sound production. Submit an audio file (song, sample, sound effect) with a summary of your workflow. |
| 3 | Three dimensions | Use an engine to do something 3-dimensional, e.g. produce a video where the Entanglement Shader has been applied to a 3D asset. |

### Intermediate — £150 prize per challenge

| # | Title | Brief |
|---|---|---|
| 4 | Moving image | Use at least one engine in a video piece. Any format. |
| 5 | Quantum game (eligible for Global Quantum Game Jam) | Use at least one engine in the making of a game, e.g. a browser game whose sprites are generated with Tessa. Bonus: submit to the Global Quantum Game Jam. |
| 6 | Daisy Chain | Use as many engines as possible in a single project. Measured on number **and** effective use. |
| 7 | Make a VST or AU | Build a music plugin using at least one engine. Submit the plugin and audio examples of it in use. |
| 8 | Make a web app | Build a web app that calls the Atlas API. Submit a link and a short description of what it does. |

### Expert — £200 prize per challenge

| # | Title | Brief |
|---|---|---|
| 9 | Quantum-native 1 | Provide a repo of a quantum application that runs a process on some kind of media (video, game, etc). Especially interested in applications that use the Atlas API. |
| 10 | Quantum-native 2 | Provide a Python notebook demonstrating how you used the API to build a workflow generating some kind of media or application. |

**Mapping to our plan's claims:** our 8-challenge claim list (build plan §3) lines
up with #1, #2, #3, #4, #6, #8, #9, #10 above. Not attempted: #5 (game) and #7
(VST/AU) — same two the plan already excluded.

## 4. Links

| Purpose | URL |
|---|---|
| RSVP (general) | https://luma.com/wmrrdpcj |
| RSVP (Friday opening) | https://luma.com/2myo5mu4 |
| Submit project | not live yet — disabled button, "Submit project" |
| Atlas platform | https://platform.mothquantum.com |
| Discord | https://discord.gg/N9y6URcYS |
| Global Quantum Game Jam | https://itch.io/jam/quantum-game-jam-2026 |

## 5. Still not in this repo

No engine catalog, no API reference, no OpenAPI spec, no per-engine parameter
docs. `content/event.ts` is copy for the public one-pager only — it confirms
challenge text, prizes and schedule, but nothing about Atlas's wire protocol.
That gap is exactly what Spencer's Saturday noon talk and our own `probe.py`
run are for. Everything in the research brief about auth, job polling, engine
slugs and Telablur's parameters is still unverified by Moth and still needs
the live catalog call.
