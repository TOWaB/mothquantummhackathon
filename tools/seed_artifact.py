#!/usr/bin/env python3
"""Seed one artifact record from data already on disk. No API calls, no credits.

    python tools/seed_artifact.py state/versions.test.json

Defaults to a .test.json file, so it never writes into live state while someone
else is building against it. Pass a path to override.

Pulls the face from manifest.json and the eight flips from api_log.jsonl, so the
page under test renders real job ids and real IBM references. Writes into
state/versions.json and prints the token to open.
"""
import json, pathlib, secrets, datetime, sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
LOG = ROOT / "state/api_log.jsonl"
MANIFEST = ROOT / "out/16_dodecahedron_faces/manifest.json"
VERSIONS = ROOT / (sys.argv[1] if len(sys.argv) > 1 else "state/versions.test.json")
FACE = 8

rows = [json.loads(l) for l in LOG.open() if l.strip()]

# the eight real flips from the first logged spin
flips = []
for r in rows:
    if r["type"] == "quantum_bit":
        res = r["result"]
        flips.append({
            "job_id": r["job_id"],
            "ibm_job_id": res["ibm_job_id"],
            "output": res["output"],
            "bit": 1 if res["output"] == "heads" else 0,
            "backend": res["backend"],
            "mode": res["mode"],
            "ts": r["ts"],
        })
    if len(flips) == 8:
        break

# the draw history, accepted and discarded
draws = next((r["bits"] for r in rows
              if r["type"] == "spin_face_picked" and r.get("bits")), [])

man = {m["face"]: m for m in json.loads(MANIFEST.read_text())}[FACE]

token = secrets.token_urlsafe(8)
record = {
    "v": 1,
    "method": "original",
    "spin_id": "e93c1aac",
    "token": token,
    "face": FACE,
    "subject": man["subject"],
    "opposite": man["opposite"],
    "params": man["params"],
    "job_id": man["job_id"],
    "elapsed_s": man["elapsed_s"],
    "floor": 0.0,
    "file": man["file"],
    "mask_file": man["file"].replace(".png", "_mask.png"),
    "flips": flips,
    "draws": draws,
    "ts": datetime.datetime.now(datetime.timezone.utc).isoformat(),
}

VERSIONS.parent.mkdir(exist_ok=True)
data = json.loads(VERSIONS.read_text()) if VERSIONS.exists() else {}
data.setdefault(str(FACE), [])
data[str(FACE)] = [r for r in data[str(FACE)] if r.get("token") != token] + [record]
VERSIONS.write_text(json.dumps(data, indent=2))

print(f"token   {token}")
print(f"flips   {len(flips)}")
print(f"draws   {len(draws)}  ({sum(1 for d in draws if not d.get('accepted'))} discarded)")
print(f"wrote   {VERSIONS.relative_to(ROOT)}")
print(f"open    http://localhost:5000/a/{token}")
