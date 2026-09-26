# Quantum Dodecahedron

**Live:** [mothhack26.visualhive.co](https://mothhack26.visualhive.co)
**Built for:** [Moth Hack 2026](https://hack.mothquantum.com)

A twelve-sided solid, each side two concert photographs mixed into each other by
a real call to Moth's Atlas API. Press the button and a quantum coin toss
decides which side changes and how. Whatever a visitor makes stays for
whoever comes next.

---

## What it is

Twelve pentagon faces on a draggable 3D solid, built in CSS transforms and one
quaternion (no Three.js). Each face holds one photograph by Petrică Tănase and
one by Cristina Tănase, who have shot the George Enescu International Festival
in Bucharest for more than ten years. Every side blends his and hers until you
cannot say where one ends.

A silhouette mask keeps the musicians themselves out of the blend at first.
Every change lifts that protection a fraction, so the people in the photos are
the last thing to dissolve.

## The challenge it answers

Entered against **Moth Hack 2026's Expert track, "Quantum-native 1"**: a repo
of a quantum application that runs a process on media, using the Atlas API.
It also stands as a working answer to the Intermediate "make a web app"
challenge — a deployed app that calls Atlas live, not just at build time.

## How the mechanic works

Two Atlas engines, both real jobs against `https://api.mothquantum.com`, both
logged with their own `job_id`:

**Picking a side — `coin-toss-v1`.** Four coin flips make a number from 0 to
15. Anything over 11 is thrown away and drawn again, because there are only
twelve sides. A flip is a real job: submit, poll, read the result — `backend
aer · mode emu`, Moth's own simulator, 2 credits and about 3.6 seconds each.
80 fresh flips run as a determinism check came back with no repeats and 45%
heads, close enough to fair that the draw is genuinely not known in advance.

**Making the picture — `telablur-v1`.** Once a side is picked, a second job
morphs one photograph into the other through the engine's own qubit rotation
circuit — 1 credit, about 7 seconds. Each new version either **rerolls**
(fresh mixing settings, starting again from the original two photographs) or
**reblends** (same settings, feeding the *current* image back in as the
starting point), decided by another quantum bit. Reblend is why the chain is
recursive: a side's twentieth version can be twenty jobs deep into itself, not
twenty independent takes on the same two source photos.

A full spin — eight flips plus one picture — is 17 credits and 46 to 48
seconds, most of it the flips rather than the picture.

**What "quantum" means here, precisely.** Every flip and every blend is a real
network call to Moth's platform, not a local random number or a canned
result — the job IDs, timings and credit costs on screen all come straight out
of `api_log.jsonl`, the append-only log that is the single source of truth for
every number the site shows. The circuits themselves run on `aer`, Moth's
simulator backend, not physical quantum hardware — the screen says so plainly
rather than implying otherwise. That distinction, and every claim of
unpredictability, is checked against a real determinism test before it's
allowed on screen; see `docs/findings.md` and `docs/06-copy.md`.

## Running it

```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt

echo "MOTH_API_KEY=moth_..." > .env    # your own Atlas API key, from platform.mothquantum.com
export $(cat .env | xargs)

flask --app app run --port 5001
```

The API key stays server-side; the browser only ever talks to this Flask app,
which proxies to Atlas and streams live events back over SSE at `/stream`.

The live deploy runs the same app via `Dockerfile`/`docker-compose.yml`
instead (behind Caddy, on its own box) — same entry point, same env var,
just containerized.

## Repo layout

| Path | What |
|---|---|
| `app.py`, `atlas.py`, `quantum.py`, `mask.py`, `floors.py`, `versions.py` | Flask app, Atlas client, the quantum draw, the dissolving mask, version history |
| `templates/`, `static/` | The viewer: the 3D solid, the live status panel, the Atlas log |
| `state/` | Mutable run state — versions, floors, what's currently served |
| `docs/` | Build notes: geometry, mask formula, copy rules, measured API numbers |
| `tools/` | Small standalone probe scripts used to test Atlas's real behaviour |

`docs/01-state-of-play.md` and `docs/findings.md` carry the measured numbers
this README repeats. If a number here and the log ever disagree, the log is
right.

## Credits

Photographs: Petrică and Cristina Tănase, George Enescu International
Festival, Bucharest, 2023. Built by TheOneWithABeard for Moth Hack 2026.

## License

MIT, with the [Commons Clause](https://commonsclause.com/) — see
[LICENSE](LICENSE). Free to use, study, run, modify and share for
non-commercial purposes; this is an art installation, not to be sold or
resold as a product or hosted service.
