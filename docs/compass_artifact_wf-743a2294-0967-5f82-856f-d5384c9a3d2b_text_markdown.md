# Moth Hack 2026 × Atlas API: Build Brief for a Claude Code Agent

Moth still hasn't published any public API docs, OpenAPI spec, SDK or Postman collection for Atlas. The most reliable public evidence of the wire protocol comes from two independent third-party codebases that have made live calls, and both agree with your notes: Bearer-key auth, a default host of `https://api.mothquantum.com`, and an async submit (HTTP 202), poll, fetch-result job model. Nothing public gives a job latency figure or any Telablur parameters. So the first hour of the build should go on measuring latency and reading the live engine catalog with your own key, before you commit to "hundreds of recursive states overnight."

## TL;DR

- **API facts:** Atlas works as an async job queue. You submit to an engine, get HTTP 202 back with a job id, poll, then download the output assets. Auth is a Bearer API key; the default host in third-party tooling is `api.mothquantum.com`. Engine ids are versioned slugs like `blur-v1`, `qrc-image-v1`, `qrc-audio-v1`, `otoc-echo-v1` and `coin-toss-v1`. Each job costs credits, and each output comes back with an `output_asset_id` you can feed into the next job without re-uploading. That last point is exactly what a recursive pipeline needs.
- **Still unknown:** Moth has published nothing on per-engine latency, rate limits, the exact Telablur engine id or its parameters. Moth's own site says the challenge links would stay disabled until the URLs exist. Get these from the live catalog call, the platform UI and Discord on Saturday morning.
- **What to do:** Build a Python `AtlasClient` with capped exponential-backoff polling and asset-id chaining. Put it behind a Flask viewer that streams job state to the browser. Write a project-level `atlas-pipeline` SKILL.md so Claude Code doesn't have to rediscover the API each session. Drop the Qiskit and K-Dense skills: they target circuit-writing, which this build doesn't do.

## Key Findings

### 1. Atlas platform: current state (verified vs. unverified)

| Item | Status | Evidence |
|---|---|---|
| Platform purpose | **Verified** | platform.mothquantum.com describes itself as the place to "run quantum engines, monitor jobs, and manage API keys." |
| Official public API docs / OpenAPI / SDK | **Not found** | Searches of mothquantum.com, github.com/moth-quantum and the hackathon repo turned up no developer docs. Docs appear to sit behind the logged-in platform. |
| Base URL `https://api.mothquantum.com` | **Likely (third-party)** | This is the default `MOTH_API_BASE` in the unofficial `mothbake` CLI (github.com/mojomast/mothbake), which can be overridden with `--base`. No official confirmation. |
| Auth | **Likely (third-party)** | `MOTH_API_KEY` is described as a "Bearer token", read from the environment only and never written to disk. |
| Async job model | **Verified by live use (third-party)** | A merged PR dated 25 Sept 2026 (SuperInstance/quilt-tools #4) ran live `coin-toss-v1` calls as "async job: 202 → poll → result", with `backend=aer` and 1 poll each, and recorded the outcome with job_id + backend + digest. |
| Engine catalog with credit costs | **Exists** | mothbake's `catalog` command lists the engines the API exposes along with their credit cost. So a catalog endpoint exists, but its path isn't documented publicly. |
| Asset chaining | **Likely** | mothbake captures each output's `output_asset_id`, and a later job can reuse it through `inputFrom`. |
| Output formats | **Likely** | mothbake decodes PNG, GIF, ZIP, Radiance HDR, WAV and MIDI engine outputs. Some engines, such as grids, echo trajectories and coin/seed results, return inline JSON instead. |
| Job statuses | **Partial** | Only `completed` is named explicitly. mothbake also handles jobs that are failed, cancelled, still running or unknown, but the exact status strings aren't confirmed. |
| Credits / quota | **Verified to exist, amounts unknown** | Every job carries a credits figure, and mothbake avoids resubmitting completed jobs precisely so it doesn't "spend credits by accident." No public credit allowance for hackathon keys. |
| Rate limits | **Unknown** | Nothing public. |
| Job latency | **Unknown** | The only data point is `coin-toss-v1` finishing within a single poll on a simulator backend (`aer`). Image engines are almost certainly slower, but nobody has published figures. |

**Engine IDs seen in public code (slug → your notes' name, by inference):**

| Slug | Likely Atlas name | Known inputs/outputs |
|---|---|---|
| `blur-v1` | Quantum Blur | input slot `image`; params `strength`, `style` (e.g. `"ry"`), `size` (e.g. 256); outputs a PNG or a value grid |
| `qrc-image-v1` | QRC Image | outputs an animated GIF |
| `qrc-audio-v1` | QRC Audio | outputs a WAV |
| `otoc-echo-v1` | Quantum Echo / Retrocausal Echo (uncertain) | trajectory JSON with taps, plus an impulse-response WAV |
| `qrc-train-v2` → `qrc-gen-v2` | QRC MIDI (two-stage) | the train job outputs a `model` asset; the gen job consumes it and outputs MIDI |
| `coin-toss-v1` | Coin Toss | inline JSON result (heads/tails) |

**Telablur is unconfirmed.** No public repo, post or doc gives its slug, input slots or parameter names. Your notes (two image assets plus an angle) fit how the concept is built in the research: James R. Wootton (IBM Research Zurich), who created Quantum Blur, wrote in his FDG 2020 paper "Procedural generation using quantum computation" (arXiv 2007.11510) that "transitions between two seed images" can be made using "a teleportation-like effect," where two images are encoded in separate qubit registers and partial SWAP operations generate the in-between frames. That's very probably where the "Tela-" (teleport) name comes from. The real parameter names (`angle`? `theta`? `fraction`?) and whether the value is in radians or 0–1 have to come from the live catalog.

**Signs the docs are gated:** a separate developer's PR dated 24 Sept 2026 quotes a sister repo saying the Moth endpoint was "undiscovered (~40 probes failed; docs live behind Casey's onboarding)." A day later the same developer had live calls working, which points to docs arriving through onboarding or Discord rather than on the public web. Your Gmail shows the Atlas account verification code arrived on 22 Sept 2026 from hello@mail.mothquantum.com, so check the platform's logged-in pages for a docs or API tab.

### 2. Moth Hack 2026 specifics

- **Format (verified, Luma page):** Moth bills it as "not a technical hackathon": you only need to use Atlas. It runs on Discord, and you can enter solo or as a team.
- **Schedule (verified):** Saturday 26 Sept, 10:00–19:00, the virtual hackathon on Discord. Sunday 27 Sept, 11:00–18:00, the exhibition and hangout at 19 D'Arblay St, London W1F 8ED. The ground floor has Quantum Backrooms and a chance to try the platform; the basement is for hanging out with staff, showcasing work and doing the challenges.
- **In-person limits:** Quantum Zeitgeist ("Drop-in Access To Quantum Apps At London's Moth Hack") reports that basement hackathon sessions need an RSVP and are limited to three-hour blocks to keep access fair, while the ground floor is open to all.
- **Prizes:** "Cash prizes to be won," plus "professional quantum advice and feedback." **No prize amounts or judging criteria have been published** anywhere public.
- **Challenge brief:** the official landing page is hack.mothquantum.com, built from github.com/moth-quantum/moth-hack-sep-2026. Its README says the submission form, Discord and challenge links render as disabled buttons until the URLs exist. The three-tier structure in your notes (Beginner / Intermediate / Expert, including "daisy chain" and "web app calling Atlas API") **couldn't be independently confirmed** from public sources. Treat your copy as authoritative and re-check it in Discord at kickoff.
- **Other participants' posts:** none found. The only public live-API evidence is the SuperInstance PRs, and they aren't hackathon entries.

### 3. Plain-language explainer for the pitch

Use these as spoken lines, not physics lectures:

- **Qubit:** a bit that isn't forced to be 0 or 1 until you look at it. It holds a *weighted blend* of both.
- **Encoding an image:** each pixel gets a binary address, which maps onto a combination of qubit states, and the pixel's brightness becomes the *amplitude* (weight) of that term. So a whole image lives in a surprisingly small number of qubits: a 256×256 image needs only 16, because 2^16 = 65,536 pixels.
- **Superposition:** after encoding, the qubits hold *every pixel at once* as one quantum state, not as a list.
- **Rotation (the "angle"):** the engine turns every qubit slightly. Small angles look like a blur; larger ones let interference take over, producing patterns an ordinary blur can't.
- **Interference:** amplitudes behave like waves. Where they line up they reinforce (bright), and where they're opposed they cancel (dark). That's why Telablur isn't a crossfade: two images meeting in a quantum state *interfere*, like ripples from two stones.
- **Measurement:** to get a picture back you have to measure, which collapses the state. The image is rebuilt from many measurement samples ("shots"), so it carries statistical grain.
- **Honesty caveat for judges:** in a December 2022 Berlin Art Link interview ("Quantum Blurs and AI Muses"), the Quantum Blur artist Roman Lipski said the process is "unpredictable but not random, since the same input always creates the same output." That holds for exact simulation. Run-to-run variation only shows up if the engine samples a finite number of shots or runs on real hardware. The coin-toss evidence shows at least some Atlas jobs run on `aer`, a simulator. **Test determinism yourself** (same inputs and angle, three runs, diff the pixels) before claiming "every run is unique."
- **Honest framing:** in "Investigating the usefulness of Quantum Blur" (arXiv 2112.01646), James Wootton and Marcel Pfaffhauser write that such behaviour "is not necessarily unique to the quantum approach" and that qualitatively similar results could "almost certainly" be achieved without quantum computing. The pitch shouldn't be "only quantum can do this." It should be "this is what quantum interference *looks* like, and our pipeline makes it explorable."

### 4. Claude Code Skills for this build

**How Skills work (verified, Anthropic docs):**
- A skill is a folder holding `SKILL.md`: YAML frontmatter between `---` markers, followed by Markdown instructions. Project skills go in `.claude/skills/<name>/SKILL.md`, and the directory name becomes the `/command`.
- `name`: max 64 characters, lowercase letters, numbers and hyphens only. `description`: max 1,024 characters. The description decides when the skill auto-loads, so list your trigger phrases in it.
- Progressive disclosure: only the name and description load at startup, about 100 tokens per skill. The body loads when the skill is relevant, and referenced files and scripts load only when they're opened or run. Scripts execute *without* their source entering context.
- Keep the SKILL.md body under 500 lines, and link to reference files at most one level deep.

**No dedicated Atlas skill exists.** No public Atlas/Moth skill turned up. The closest reference implementations are mothbake (Node, zero dependencies) and the quilt-tools coin-toss experiment. Clone mothbake and let Claude Code read its HTTP client and mock-API test: the README says its offline HTTP test runs against a local mock that serves recorded fixtures, so it encodes the real route shapes.

**Qiskit and K-Dense skills: confirmed irrelevant.** The K-Dense `qiskit` skill covers building, transpiling and executing circuits, and was verified in July 2026 against qiskit 2.5.0. IBM's official Qiskit Agent Skills are also for Qiskit and IBM Runtime workflows. Neither touches a REST job-queue API. Leave both uninstalled so they don't auto-trigger and steer the agent toward writing circuits. The only exception is the Expert "quantum-native repo/notebook" tier, if you pivot to it.

**Generic async-polling pattern to encode:** use capped exponential backoff with jitter. Marc Brooker's Amazon Builders' Library article "Timeouts, retries, and backoff with jitter" calls capped exponential backoff Amazon's preferred approach and adds jitter to spread retries out, which is what prevents synchronized retry storms. Honor `Retry-After` if the server sends it. Treat 202 as "accepted," not "succeeded." Set a hard overall timeout. Never resubmit a job just because a poll failed, since that spends credits twice.

## Recommendations

### A. Hour-one checklist (before writing pipeline code)

1. **Get the catalog:** run `MOTH_API_KEY=… node bin/mothbake.mjs catalog` from a mothbake clone, or look in the platform UI. Save the JSON to `docs/atlas-catalog.json`. This one step settles engine slugs, Telablur's parameters and credit costs.
2. **Discover the routes:** read mothbake's `src/` client and `test/` mock to get the exact submit, poll, asset-upload and download paths. Write them into `reference/api.md`.
3. **Probe latency:** submit five sequential jobs for each engine you plan to use (Telablur, Quantum Blur, and your audio engine). Log submit→complete wall time, number of polls and credits. Record p50 and p95.
4. **Check determinism:** run Telablur three times with identical inputs and the same angle, then compute the pixel difference.
5. **Check your credit budget:** read your balance before and after the probe, and divide to get runs per credit.

### B. Latency decides the scope of the recursive plan

Sequential capacity over roughly an 8-hour overnight window:

| p50 job time | Sequential states / 8 h | Verdict |
|---|---|---|
| 10 s | ~2,880 | "Hundreds" is easy |
| 30 s | ~960 | Comfortable |
| 2 min | ~240 | Just about "hundreds" |
| 5 min+ | ≤96 | Redesign needed |

Where the numbers fall short, change the design this way:
- **A recursive chain is inherently sequential**, because state N+1 needs output N. The fix is *several independent lineages in parallel*, e.g. 4–8 chains seeded differently or run at different angles, not a faster single chain. Test the concurrency limit carefully, because the rate limits are unknown.
- **Credits may run out before time does.** Put a hard `MAX_JOBS` or credit ceiling in config.
- **The live viewer shouldn't block on Atlas.** Precompute the overnight chain, and let the live view (a) replay cached states and (b) fire one fresh "branch" job on demand, with a visible queued→running→collapsed status. Round trips of minutes make a fully live-only demo risky in front of judges.
- **Chain by asset id:** pass `output_asset_id` straight into the next job instead of downloading and re-uploading. Download only for display and archiving.

### C. Recommended project SKILL.md (`.claude/skills/atlas-pipeline/SKILL.md`)

```markdown
---
name: atlas-pipeline
description: Build and run against Moth Atlas quantum engines via REST. Use when submitting Atlas jobs, polling job status, uploading/chaining assets, running the recursive Telablur/Quantum Blur state pipeline, or editing the Flask live viewer. Triggers: atlas, moth, engine, telablur, quantum blur, job id, poll, asset id, recursive state, viewer.
---
# Atlas pipeline

## Ground truth (read first)
- Engine slugs, params, credit costs: docs/atlas-catalog.json (generated by catalog call; never guess param names).
- Routes, status strings, payload shapes: reference/api.md.
- Measured latency/credits: reference/latency.md. Plan batch sizes from p95, not hopes.

## Hard rules
1. Auth: header `Authorization: Bearer $MOTH_API_KEY`; key from env/.env only; never log, commit, or send to the browser (Flask proxies all Atlas calls server-side).
2. Base URL from env `MOTH_API_BASE` (default https://api.mothquantum.com).
3. Submit → expect 202 + job id → poll with capped exponential backoff + jitter (start 2s, x1.5, cap 30s, overall timeout from config), honor Retry-After. 202 ≠ success.
4. Never resubmit on poll error; re-poll the same job id. Persist every job id to state/jobs.jsonl before polling (crash-safe resume).
5. Chain states via output_asset_id; download outputs only for display/archive.
6. Respect MAX_JOBS and MAX_CONCURRENCY from config.yaml; stop cleanly when exceeded.
7. If a param/slug is missing from the catalog, stop and ask — do not invent.

## Code map
- atlas/client.py — AtlasClient: catalog(), upload(path)->asset_id, submit(engine, inputs, params)->job_id, wait(job_id)->job, download(asset_id, dest).
- pipeline/recurse.py — state loop: state_n asset -> engine -> state_n+1; writes state/NNNN.json {job_id, engine, params, input_asset_ids, output_asset_id, credits, t_submit, t_done, file}.
- viewer/app.py — Flask; /api/states (list), /api/branch (POST, fires one job), /stream (SSE job status); static gallery.
- scripts/probe_latency.py — runs N jobs/engine, writes reference/latency.md.

## Testing
- Offline first: tests use recorded fixtures in tests/fixtures/ with a mocked HTTP layer; no live calls in unit tests.
- Live smoke test: `python scripts/smoke.py` (one coin-toss-class cheap job) before any batch.
```

Add these supporting files, which load only when needed: `reference/api.md` (routes, verified from mothbake source), `reference/latency.md` (from the probe), `docs/atlas-catalog.json`, and `reference/pitch.md` (the plain-language explainer above, so the agent writes on-screen captions that match the pitch).

### D. Flask viewer pattern

- Keep all Atlas calls on the server. The browser only ever talks to Flask, so the key never leaves it.
- Use Server-Sent Events (or a 2–5 s client poll of `/api/states`) to push job transitions. Label them in quantum terms for the audience: *queued → superposed (running) → collapsed (done)*.
- Show each state's provenance (engine, angle, job id, credits, time taken). It makes "this ran on Atlas" concrete to judges and satisfies any "daisy chain / max engines" criterion.

## Caveats

- **Everything about the wire protocol is third-party-derived.** The protocol details come from mothbake, and the only live-call evidence is the quilt-tools PR. Neither is affiliated with Moth, and either could lag behind API changes. The live catalog and platform docs override this report.
- **Telablur's slug, parameters, input count and determinism are unverified.** The "two images + angle, interference not crossfade" description fits the SWAP/teleportation-blend technique James R. Wootton published in "Procedural generation using quantum computation" (FDG 2020, arXiv 2007.11510), but no Moth source confirms it.
- **The "30 engines" count and the engine groupings in your notes couldn't be confirmed publicly,** and neither could the three-tier challenge brief. Your mapping of slugs to Atlas display names (e.g. `otoc-echo-v1` → Quantum Echo) is inferred.
- **Prize amounts and judging criteria are unpublished.** Ask in Discord at kickoff.
- **The `backend=aer` evidence** means at least some jobs run on a classical simulator of a quantum computer, not on QPU hardware. If you claim "real quantum hardware" in the pitch, confirm the backend for your specific engine first.