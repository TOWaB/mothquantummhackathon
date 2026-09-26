"""
Flask live viewer — the dodecahedron web app (challenge #8).

Visitor spins a 12-faced object on screen. Every face-pick and every
reroll/reblend decision is made by a *real* quantum coin toss
(quantum.quantum_choice / quantum_bit), run live, with every single Atlas
API call streamed to the browser's log panel in real time via
atlas.log_event / atlas.read_log — nothing here is faked or pre-baked at
request time.

Each spin runs in a background thread (a face-pick alone is 3-4 quantum
coin tosses at ~7-10s each, plus a possible telablur regen job) so the
frontend can poll /api/log continuously and render the quantum decisions as
they happen, instead of staring at a blank screen for 30-60s.

Run with: uv run --python .venv app.py
"""
import json
import queue
import random
import threading
import uuid
from pathlib import Path

import requests
from flask import Flask, Response, jsonify, request, send_from_directory, stream_with_context

import atlas
import floors
import mask
import quantum
import versions

BASE = Path(__file__).parent
FACES_SRC = BASE / "out/16_dodecahedron_faces"
FACES_MANIFEST = FACES_SRC / "manifest.json"
STATIC_FACES = BASE / "static/faces"
STATIC_FACES.mkdir(parents=True, exist_ok=True)
IMAGES_DIR = BASE / "images"

SERVED_PATH = BASE / "state/served.json"
SERVED_PATH.parent.mkdir(exist_ok=True)

RADII = [15, 30, 45, 60, 90]
STRENGTHS = [0.1, 0.2, 0.3]
DIRECTIONS = ["full", "vertical", "horizontal"]

app = Flask(__name__)

_lock = threading.Lock()
SPINS: dict[str, dict] = {}

# SSE subscribers for /stream. Registered into atlas.py's broadcast hook so
# every atlas.log_event call anywhere (this file, quantum.py, probe scripts)
# reaches connected browsers live, with zero changes to those call sites.
subscribers: list[queue.Queue] = []
_sub_lock = threading.Lock()


def _broadcast(event: dict):
    line = json.dumps(event)
    with _sub_lock:
        for q in list(subscribers):
            try:
                q.put_nowait(line)
            except queue.Full:
                pass


atlas.subscribe(_broadcast)


def load_faces() -> dict:
    """(Re)load face state from the generation manifest + any regenerations
    already recorded in state/served.json. Safe to call while the background
    generation script is still filling in later faces."""
    faces = {}
    if FACES_MANIFEST.exists():
        for entry in json.loads(FACES_MANIFEST.read_text()):
            if entry.get("status") != "completed":
                continue
            n = entry["face"]
            faces[n] = {
                "face": n,
                "subject": entry["subject"],
                "opposite": entry["opposite"],
                "params": entry["params"],
                "job_id": entry["job_id"],
                "file": f"face{n:02d}.png",
            }
    served = load_served()
    for n, s in served.get("current", {}).items():
        faces[int(n)] = s
    for n, info in faces.items():
        src = FACES_SRC / info["file"] if info["file"].startswith("face") and "/" not in info["file"] else Path(info["file"])
        dest = STATIC_FACES / f"face{n:02d}.png"
        if src.exists() and (not dest.exists() or src.stat().st_mtime > dest.stat().st_mtime):
            dest.write_bytes(src.read_bytes())
        # version 1 is always the baked original and never changes — keep a
        # permanent _v1 copy so the version list can load it like any other
        # version, the same as reroll/reblend get face{NN}_v{N}.png.
        v1_dest = STATIC_FACES / f"face{n:02d}_v1.png"
        if src.exists() and not v1_dest.exists():
            v1_dest.write_bytes(src.read_bytes())
    return faces


def load_served() -> dict:
    if SERVED_PATH.exists():
        return json.loads(SERVED_PATH.read_text())
    return {"current": {}}


def save_served(served: dict):
    SERVED_PATH.write_text(json.dumps(served, indent=2))


def _fail(spin_id: str, kind: str, message: str):
    atlas.log_event({"type": "spin_error", "spin_id": spin_id, "kind": kind, "error": message})
    SPINS[spin_id] = {"status": "error", "kind": kind, "error": message}


def run_spin(spin_id: str):
    """Wraps _run_spin_inner so a real network error or job failure surfaces
    as one of the four states in docs/06-copy.md instead of silently killing
    the background thread and leaving SPINS[spin_id] stuck at "running"
    forever (that was a real gap — nothing here caught exceptions at all)."""
    try:
        _run_spin_inner(spin_id)
    except requests.exceptions.RequestException as e:
        _fail(spin_id, "unreachable", str(e))
    except RuntimeError as e:
        kind = "credits" if "credit" in str(e).lower() else "job_failed"
        _fail(spin_id, kind, str(e))
    except Exception as e:
        _fail(spin_id, "job_failed", str(e))


def _run_spin_inner(spin_id: str):
    atlas.log_event({"type": "spin_start", "spin_id": spin_id})
    bit_log = []
    face_options = list(range(1, 13))
    face = quantum.quantum_choice(face_options, log=bit_log)
    atlas.log_event({"type": "spin_face_picked", "spin_id": spin_id, "face": face, "bits": bit_log})

    # B3/B4: step this face's mask floor, direction from the discarded draw
    # (docs/02-quantum-open.md Q5's suggestion — those bits are already paid
    # for). Every landing steps it, win or repeat, per Q8: the sides people
    # spin on are the ones that erode.
    discarded = [b for entry in bit_log if not entry["accepted"] for b in entry["bits"]]
    accepted = next((entry["bits"] for entry in bit_log if entry["accepted"]), [])
    direction = floors.walk_step(discarded, accepted)
    new_floor = floors.step_floor(face, direction)
    atlas.log_event({"type": "floor_stepped", "spin_id": spin_id, "face": face, "direction": direction, "floor": new_floor})

    faces = load_faces()
    info = faces.get(face)

    if info is None:
        SPINS[spin_id] = {"status": "error", "error": f"face {face} not generated yet"}
        return

    # docs/mask-tasks: a visitor press always rebakes now — no more free
    # "first landing shows the untouched original" branch. The interface's
    # own claim ("Change a side" / "stays that way for whoever comes next")
    # is false for a press that lands on `original`, so that outcome no
    # longer exists for a live press; `original` survives only as the label
    # already seeded onto every face's version-1 entry. This also means a
    # floor-step and a version always happen together, 1:1 — no separate
    # fix needed for that.
    method = "reblend" if quantum.quantum_bit() == 1 else "reroll"
    atlas.log_event({"type": "spin_method_picked", "spin_id": spin_id, "face": face, "method": method})

    subject_path = STATIC_FACES.parent.parent / "out/16_dodecahedron_faces" / f"face{face:02d}_subject.png"
    opposite_path = STATIC_FACES.parent.parent / "out/16_dodecahedron_faces" / f"face{face:02d}_opposite.png"
    subject_asset = atlas.upload_asset(subject_path)
    opposite_asset = atlas.upload_asset(opposite_path)

    # Hoisted ahead of the job (docs/mask-tasks M2): the mask/version number
    # need to exist before the job even starts, not after it completes, so
    # the mask can be shown live during the ~7s wait. Safe to compute this
    # early because spins are serialized server-side (see /api/spin) — no
    # other writer can append to this face's version list in between.
    next_v = len(versions.load_versions().get(str(face), [])) + 1

    if method == "reroll":
        radius = quantum.quantum_choice(RADII, log=bit_log)
        strength = quantum.quantum_choice(STRENGTHS, log=bit_log)
        direction = quantum.quantum_choice(DIRECTIONS, log=bit_log)
        alpha = mask.segment_person(subject_path)
        gradient = mask.make_mask(alpha, radius=radius, floor=new_floor)
        params = {"strength": strength, "direction": direction, "mask_radius": radius, "mask_type": "distance_gradient"}
        image1_asset = subject_asset
    else:  # reblend: same params, feed the CURRENT image back in as image1
        params = dict(info["params"])
        current_path = STATIC_FACES / f"face{face:02d}.png"
        image1_asset = atlas.upload_asset(current_path)
        radius = params.get("mask_radius", 30)
        alpha = mask.segment_person(subject_path)
        gradient = mask.make_mask(alpha, radius=radius, floor=new_floor)

    # The real masking input Atlas consumes — plain grayscale, a throwaway
    # reused path (safe: spins are serialized, nothing else writes this
    # concurrently). Never the ring-annotated version below; telablur reads
    # this file's pixel values as data, and the ring would corrupt that.
    upload_mask_path = STATIC_FACES / "_upload_mask.png"
    gradient.save(upload_mask_path)
    mask_asset = atlas.upload_asset(upload_mask_path)

    # The permanent, servable preview — ring-annotated, this is what's ever
    # stored in versions.json and shown on screen (docs/mask-tasks M2/M3.4).
    mask_name = f"face{face:02d}_v{next_v}_mask.png"
    mask.ring_overlay(gradient, alpha).save(STATIC_FACES / mask_name)

    atlas.log_event({
        "type": "spin_mask_ready", "spin_id": spin_id, "face": face,
        "method": method, "v": next_v, "floor": new_floor, "mask_file": mask_name,
    })

    job_id = atlas.submit_job(
        "telablur-v1",
        {"strength": params["strength"], "direction": params["direction"]},
        {"image1": image1_asset, "image2": opposite_asset, "mask": mask_asset},
    )
    st, elapsed = atlas.wait_for_job(job_id, engine="telablur-v1")
    if st["status"] != "completed":
        SPINS[spin_id] = {"status": "error", "error": st.get("error")}
        return

    result = atlas.fetch_result(job_id)
    # Naming convention is docs/08-structure.md's own: face{NN}_v{N}.png keeps
    # every version's actual pixels on disk (not just its metadata), so the
    # version list can genuinely "load that version" instead of only ever
    # showing whatever regeneration happened to run last.
    versioned_name = f"face{face:02d}_v{next_v}.png"
    versioned_path = STATIC_FACES / versioned_name
    current_path_out = STATIC_FACES / f"face{face:02d}.png"
    for out in result.get("outputs") or []:
        data = requests.get(out["url"], timeout=atlas.HTTP_TIMEOUT).content
        versioned_path.write_bytes(data)
        current_path_out.write_bytes(data)

    new_info = {
        "face": face, "subject": info["subject"], "opposite": info["opposite"],
        "params": params, "job_id": job_id, "file": f"face{face:02d}.png",
        "floor": new_floor,
    }
    served = load_served()
    served["current"][str(face)] = new_info
    save_served(served)

    logged = atlas.log_event({"type": "spin_result", "spin_id": spin_id, "face": face, "method": method, "job_id": job_id, "elapsed_s": round(elapsed, 1)})
    versions.append_version(face, method, job_id, params, round(elapsed, 1), new_floor, logged["ts"], versioned_name, mask_file=mask_name)
    SPINS[spin_id] = {"status": "done", "face": face, "method": method, "image": f"/static/faces/face{face:02d}.png?v={job_id}", "job_id": job_id, "params": params, "floor": new_floor, "mask_file": mask_name}


@app.route("/")
def index():
    return send_from_directory(BASE / "templates", "index.html")


@app.route("/api/faces")
def api_faces():
    faces = load_faces()
    return jsonify({str(n): {"face": n, "ready": True} for n in faces})


_active_spin_id = None  # the one spin currently running, or None


@app.route("/api/spin", methods=["POST"])
def api_spin():
    """Rejects a second spin outright rather than queuing one — this is one
    shared object everyone watches live via /stream, not a personal-turn
    system, so "someone else is already spinning it, watch" is the honest
    behaviour, not "you're #2 in line." Also the thing that actually
    prevents the real race this was guarding against: served.json,
    floors.json and versions.json are all unlocked read-modify-write, and
    two spins landing on the same face at the same time could corrupt
    version numbering. Serializing spins server-side fixes that too, for
    free, without needing per-file locks."""
    global _active_spin_id
    with _lock:
        if _active_spin_id is not None and SPINS.get(_active_spin_id, {}).get("status") == "running":
            return jsonify({"error": "spin_in_progress", "spin_id": _active_spin_id}), 409
        spin_id = uuid.uuid4().hex[:8]
        _active_spin_id = spin_id
        SPINS[spin_id] = {"status": "running"}
    threading.Thread(target=run_spin, args=(spin_id,), daemon=True).start()
    return jsonify({"spin_id": spin_id})


@app.route("/api/spin/<spin_id>")
def api_spin_status(spin_id):
    return jsonify(SPINS.get(spin_id, {"status": "unknown"}))


def _counters_since_reset() -> dict:
    """Every number here traces to a line in state/api_log.jsonl — computed
    by scanning it, not maintained as separate incremental state that could
    drift from the log. Scoped to events after the most recent `reset`
    marker so /reset can give a real zero without ever truncating the log
    (which stays append-only, full history intact for Track F3)."""
    events = atlas.read_log(limit=1_000_000)
    last_reset_ts = None
    for e in reversed(events):
        if e["type"] == "reset":
            last_reset_ts = e["ts"]
            break
    since = [e for e in events if last_reset_ts is None or e["ts"] > last_reset_ts]
    return {
        "flips": sum(1 for e in since if e["type"] == "quantum_bit"),
        "spins": sum(1 for e in since if e["type"] == "spin_start"),
        "credits": sum(e.get("credits", 0) for e in since if e["type"] == "submit"),
        "versions": sum(len(v) for v in versions.load_versions().values()),
    }


def _face_pairing() -> dict:
    """face number -> its opposite face's number, from manifest.json. Every
    'opposite' photo is itself some other face's own 'subject' photo
    (confirmed directly against the real pairing) — subject/opposite are a
    face-level constant, the same across every version of that face, which
    is why they were never stored per-version in versions.json. This lets
    the screen say "Face 7" for both photo rows instead of a raw filename,
    or nothing at all (version entries never carried the filenames)."""
    if not FACES_MANIFEST.exists():
        return {}
    manifest = json.loads(FACES_MANIFEST.read_text())
    photo_to_face = {entry["subject"]: entry["face"] for entry in manifest}
    return {entry["face"]: photo_to_face.get(entry["opposite"]) for entry in manifest}


@app.route("/state")
def state():
    faces = load_faces()
    served = load_served()
    return jsonify({
        "counters": _counters_since_reset(),
        "faces": served.get("current", {}),
        "faces_ready": len(faces),
        "versions": versions.load_versions(),
        "face_pairing": _face_pairing(),
    })


@app.route("/reset", methods=["POST"])
def reset():
    atlas.log_event({"type": "reset"})  # marker only — log stays append-only
    save_served({"current": {}})
    floors.save_floors({str(n): 0.0 for n in range(1, 13)})
    versions.reset_to_manifest()
    for n in range(1, 13):
        src = FACES_SRC / f"face{n:02d}.png"
        if src.exists():
            data = src.read_bytes()
            (STATIC_FACES / f"face{n:02d}.png").write_bytes(data)
            (STATIC_FACES / f"face{n:02d}_v1.png").write_bytes(data)
            for old in STATIC_FACES.glob(f"face{n:02d}_v[!1]*.png"):
                old.unlink()
    SPINS.clear()
    return jsonify({"ok": True})


@app.route("/stream")
def stream():
    q = queue.Queue(maxsize=256)
    with _sub_lock:
        subscribers.append(q)

    @stream_with_context
    def gen():
        try:
            yield ": connected\n\n"
            while True:
                try:
                    line = q.get(timeout=20)
                    yield f"data: {line}\n\n"
                except queue.Empty:
                    yield ": keepalive\n\n"
        finally:
            with _sub_lock:
                if q in subscribers:
                    subscribers.remove(q)

    return Response(gen(), mimetype="text/event-stream",
                     headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"})


@app.route("/api/log")
def api_log():
    since = int(request.args.get("since", 0))
    all_events = atlas.read_log(limit=10000)
    return jsonify({"events": all_events[since:], "total": len(all_events)})


@app.route("/static/faces/<path:filename>")
def static_faces(filename):
    return send_from_directory(STATIC_FACES, filename)


if __name__ == "__main__":
    load_faces()
    # threaded=True is required, not optional: an open /stream connection
    # blocks Werkzeug's single-threaded dev server for its whole lifetime
    # otherwise, and no other request (including /api/spin) could be served
    # while a visitor has the page open.
    app.run(host="0.0.0.0", port=5001, debug=False, use_reloader=False, threaded=True)
