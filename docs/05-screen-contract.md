# 05. Screen contract

Every id already in `templates/index.html` survives. Everything new is additive, so `app.js` keeps running while the screen is rebuilt around it.

---

## One event stream, two sinks

`app.js` already writes seven event types to `api_log.jsonl`. The screen renders the same objects, unchanged. No second format, no translation layer.

Server writes the line to disk and pushes it down `/stream`. The front end has one switch.

| Event | What the screen does |
|---|---|
| `spin_start` | clear the ladder, start the clock |
| `submit` | log row, engine and credits, start the poll counter |
| `complete` | log row with `elapsed_s` |
| `quantum_bit` | land one rung: heads or tails, `job_id`, `ibm_job_id` |
| `spin_face_picked` | render accepted and discarded draws, highlight the side |
| `spin_method_picked` | show `original`, `reroll` or `reblend` |
| `spin_result` | fill the face panel, bump the counters |

`spin_face_picked` already carries the whole draw history in `bits`, including `accepted: false`. The discard story is already in the data.

---

## Endpoints

| Route | Returns |
|---|---|
| `GET /stream` | SSE, one event per JSONL line, shape unchanged |
| `POST /spin` | `{spin_id}` immediately, does not block |
| `GET /state` | counters and the current version per side, for a mid-exhibition refresh |
| `GET /pool` | bits remaining, if the pool from Q4 gets built |
| `POST /reset` | zero the counters, back to the baked manifest faces |

`POST /spin` returning immediately is what makes a 48 second wait watchable rather than a hung request.

### Flask

```python
import json, queue, threading
from flask import Response, stream_with_context

subscribers = []           # list[queue.Queue]
_lock = threading.Lock()

def emit(event: dict):
    """Call this everywhere you already append to api_log.jsonl."""
    line = json.dumps(event)
    with open("api_log.jsonl", "a") as f:
        f.write(line + "\n")
    with _lock:
        for q in list(subscribers):
            q.put_nowait(line)

@app.route("/stream")
def stream():
    q = queue.Queue(maxsize=256)
    with _lock:
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
            with _lock:
                if q in subscribers:
                    subscribers.remove(q)

    return Response(gen(), mimetype="text/event-stream",
                    headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"})

@app.post("/spin")
def spin():
    spin_id = uuid.uuid4().hex[:8]
    threading.Thread(target=run_spin, args=(spin_id,), daemon=True).start()
    return {"spin_id": spin_id}, 202
```

### Front end

```js
const es = new EventSource("/stream");
es.onmessage = e => renderEvent(JSON.parse(e.data));

function renderEvent(ev) {
  logLine(ev.ts.slice(11, 19), ev.type, describe(ev));
  switch (ev.type) {
    case "spin_start":        clearLadder(); startClock(); break;
    case "submit":            bumpCredits(ev.credits); break;
    case "quantum_bit":       landRung(ev.job_id, ev.result); break;
    case "spin_face_picked":  renderDraws(ev.bits, ev.face); break;
    case "spin_result":       showFace(ev.face); break;
  }
}

// falls back to polling if SSE is blocked by anything in the room
es.onerror = () => { es.close(); setInterval(() => fetch("/state").then(r => r.json()).then(applyState), 2000); };
```

The fallback matters. An exhibition network is not a development network.

---

## Markup

Existing ids kept in the same nesting order. New ids marked.

```html
<header id="topbar">                                <!-- new -->
  <span class="brand"><i class="sq"></i> Visual Hive</span>
  <h1>Quantum Dodecahedron</h1>
  <button id="resetBtn" class="ghost">Start again</button>
</header>

<div id="viewer">
  <div id="credits-bar">
    Credits spent this session: <b id="credits">0</b>
    <span id="counters">                            <!-- new -->
      <span><b id="c-flips">0</b>coin flips</span>
      <span><b id="c-versions">0</b>versions made</span>
      <span><b id="c-spins">0</b>spins</span>
    </span>
    <div id="claim">Every side here was chosen by a flip on Atlas, and every flip has a job id.</div>
  </div>

  <div id="engine-line">                            <!-- new, read from the response -->
    Side picked by four <span class="m">coin-toss-v1</span> flips, picture from
    <span class="m">telablur-v1</span>. <span class="m">backend aer · mode emu</span>
  </div>

  <div id="stage"></div>                            <!-- Dodeca() mounts here -->

  <div id="facepanel">                              <!-- new -->
    <img id="faceimg" alt="">
    <div id="facemeta"></div>
    <div id="versions"><div id="vlist"></div></div>
  </div>

  <button id="spinBtn">Spin it</button>

  <div id="status">                                 <!-- kept, contents replaced -->
    <div id="stage-line">Ready. Press spin.</div>
    <div id="poll-line">Four flips pick the side, about 3.6 seconds each.</div>
    <div id="clock-line"></div>
  </div>

  <div id="ladder"><div id="ladder-rows"></div></div>   <!-- new -->

  <div id="overlay">
    <div><b class="proof-face"></b> — <span class="proof-method"></span></div>
    <div>job: <span class="proof-job"></span></div>
    <div>params: <span class="proof-params"></span></div>
  </div>
</div>

<div id="log-panel">
  <h2>Atlas log</h2>
  <div id="log"></div>
</div>
```

---

## Layout at the exhibition

Three columns on a laptop, stacked on a phone.

| Column | Holds |
|---|---|
| Left | the solid |
| Middle | Facing you: image first, then settings rows, then the version strip |
| Right | Spin it, the three status lines, the coin flips, the log |

The right column is the wait, in the order it happens. During a spin it is the only thing anyone looks at, so it gets the flips landing one at a time rather than a spinner.

---

## Colour and type

Visual Hive Signal tokens.

```css
:root {
  --paper:#ffffff; --ink:#141414; --signal:#f0f22e; --circuit:#4634e0;
  --slate:#6a696d; --steel:#7b7d86; --mist:#d3d6d8; --track:#f0f0f1;
}
```

Inter Tight for anything readable, JetBrains Mono for ids, timestamps and log rows. Yellow appears once per screen state, on the active thing. Violet carries job ids, elapsed times and credits, nothing else. `#stage` sits on ink and everything around it is white.
