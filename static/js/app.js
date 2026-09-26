/* One renderEvent(e) switch over the seven-plus event types in
 * state/api_log.jsonl (docs/05-screen-contract.md), driving the ladder, the
 * face panel, the three-line status, and the log — instead of a flat
 * scrolling text list. Every string here is from docs/06-copy.md. */

// els/METHOD/ROWS/the state `let`s must all be declared before Dodeca() is
// constructed below: its constructor calls onFace synchronously (whatever
// face fronts the initial orientation), which calls onFaceSelected, which
// touches these. Referencing a `let`/`const` before its own declaration
// line has run throws a real ReferenceError (not just "undefined") — this
// crashed the whole script on load until reordered. See LEARNINGS.md.
const els = {
  autoSpinBtn: document.getElementById("autoSpinBtn"),
  spinBtn: document.getElementById("spinBtn"),
  stageLine: document.getElementById("stage-line"),
  pollLine: document.getElementById("poll-line"),
  clockLine: document.getElementById("clock-line"),
  ladder: document.getElementById("ladder-rows"),
  log: document.getElementById("log"),
  faceimg: document.getElementById("faceimg"),
  facename: document.getElementById("facename"),
  faceversion: document.getElementById("faceversion"),
  facesub: document.getElementById("facesub"),
  facecredit: document.getElementById("facecredit"),
  facerows: document.getElementById("facerows"),
  vlist: document.getElementById("vlist"),
  maskToggle: document.getElementById("maskToggle"),
  floorstrip: document.getElementById("floorstrip"),
  intro: document.getElementById("intro"),
  introToggle: document.getElementById("introToggle"),
  cFlips: document.getElementById("c-flips"),
  cVersions: document.getElementById("c-versions"),
  cSpins: document.getElementById("c-spins"),
  claim: document.getElementById("claim"),
};

const METHOD = {
  original: "the photograph on its own, nothing mixed in yet",
  reroll: "run again with new settings, same two photos",
  reblend: "run again with the same settings, blending onto the last result",
};

const ROWS = [
  ["First photo", "subject", (p, face) => `Face ${face}`, false,
    (p, face) => photographer(latestState?.face_photos?.[face]?.subject)],
  ["Second photo", "opposite", (p, face) => `Face ${(latestState && latestState.face_pairing[face]) ?? "?"}`, false,
    (p, face) => photographer(latestState?.face_photos?.[face]?.opposite)],
  ["How much mixing", "strength", p => p.params.strength],
  ["Which way it mixes", "direction", p => p.params.direction],
  ["How wide it spreads", "mask_radius", p => p.params.mask_radius],
  ["Job", "job_id", p => p.job_id, true],
  ["Took", "elapsed_s", p => (p.elapsed_s != null ? p.elapsed_s + "s" : "—")],
];

// docs/TASKS-final-ui.md §1: filename prefix identifies the photographer.
// subject/opposite are face-level constants (same pair every version, see
// app.py's _face_photos), so this only ever needs latestState.face_photos.
function photographer(filename) {
  if (!filename) return null;
  if (filename.startsWith("2V0")) return "Cristina Tănase";
  if (filename.startsWith("H66")) return "Petrică Tănase";
  return null;
}

function creditLine(face) {
  const photos = latestState && latestState.face_photos && latestState.face_photos[face];
  if (!photos) return "";
  const a = photographer(photos.subject);
  const b = photographer(photos.opposite);
  const names = a && b && a !== b
    ? "Petrică Tănase and Cristina Tănase"
    : (a || b);
  if (!names) return "";
  return `${names} · George Enescu International Festival, 2023`;
}

let counters = { flips: 0, versions: 0, spins: 0 };
let currentFace = 1;
let latestState = null; // last GET /state response, refreshed after every spin_result
let pickingFace = false;
let drawIndex = 0;
let rungInDraw = 0;
let currentDrawEl = null;
let spinClockTimer = null;
let spinClockStart = 0;
let frontFace = 1; // whatever face is actually fronting, including at construction
let currentDrawBits = []; // this draw's bits so far, to detect a live "thrown away" (docs/TASKS-site-copy.md §3)
const floorFills = {};
const floorCells = {};

const dodeca = Dodeca(document.getElementById("stage"), {
  size: 190,
  onFace: n => onFaceSelected(n),
});
console.assert(dodeca.checkGeometry().ok, "dodecahedron does not close");

function fmtTime(ts) {
  return new Date(ts).toLocaleTimeString("en-GB", { hour12: false });
}

function bumpCounters() {
  els.cFlips.textContent = counters.flips;
  els.cVersions.textContent = counters.versions;
  els.cSpins.textContent = counters.spins;
  // docs/TASKS-site-copy.md §3: that counter is gone from the screen
  // entirely now, five becomes four — no display element for it anymore.

  // This session's own real flips, not a frozen claim from one past test
  // run (see docs/06-copy.md) — no "no repeats" claim, since that isn't
  // something cheap to verify live across every flip ever made.
  if (els.claim) {
    els.claim.textContent = counters.flips
      ? `Every side is chosen by a flip nobody can predict. ${counters.flips} real flip${counters.flips === 1 ? "" : "s"} so far this session, ${counters.heads_pct}% heads.`
      : "Every side is chosen by a flip nobody can predict.";
  }
}

function logRow(ev) {
  const row = document.createElement("div");
  row.className = "l";
  const tyClass = ev.type === "submit" ? "ty sub" : ev.type === "complete" ? "ty cmp" : "ty";
  row.innerHTML =
    `<span class="t">${fmtTime(ev.ts)}</span><span class="${tyClass}">${ev.type}</span><span class="d"></span>`;
  row.querySelector(".d").textContent = describe(ev);
  els.log.appendChild(row);
  els.log.scrollTop = els.log.scrollHeight;
}

function describe(ev) {
  switch (ev.type) {
    case "spin_start":
      return `spin_id ${ev.spin_id}`;
    case "submit":
      return `${ev.engine} · ${ev.job_id.slice(0, 8)} · ${JSON.stringify(ev.params)} · ${ev.credits}cr`;
    case "complete":
      return `${ev.engine || ""} · ${ev.job_id.slice(0, 8)} · ${ev.status} · ${ev.elapsed_s}s`;
    case "quantum_bit":
      return `${ev.result.output} · ibm ${(ev.result.ibm_job_id || "").slice(0, 16)} · ${ev.result.backend}/${ev.result.mode}`;
    case "spin_face_picked":
      return `${ev.bits.map(b => `idx ${b.idx} ${b.accepted ? "accepted" : "rejected"}`).join(", ")}, face ${ev.face}`;
    case "spin_method_picked":
      return `face ${ev.face} · ${ev.method}`;
    case "spin_mask_ready":
      return `face ${ev.face} · v${ev.v} · floor ${ev.floor}`;
    case "spin_result":
      return `face ${ev.face} · ${ev.method}${ev.elapsed_s != null ? " · " + ev.elapsed_s + "s" : ""}`;
    case "spin_error":
      return `${ev.kind} · ${ev.error}`;
    case "floor_stepped":
      return `face ${ev.face} · floor ${ev.floor}`;
    case "reset":
      return "counters zeroed, log kept";
    default:
      return JSON.stringify(ev);
  }
}

/* ---- the coin-flip ladder ------------------------------------------- */
function clearLadder() {
  els.ladder.innerHTML = "";
  drawIndex = 0;
  rungInDraw = 0;
  currentDrawEl = null;
}

const ORDINAL = ["First", "Second", "Third", "Fourth", "Fifth", "Sixth"];

function landRung(ev) {
  if (rungInDraw === 0) {
    currentDrawEl = document.createElement("div");
    currentDrawEl.className = "draw";
    const lab = document.createElement("div");
    lab.className = "dlab";
    lab.textContent = `${ORDINAL[drawIndex] || drawIndex + 1 + "th"} go`;
    currentDrawEl.appendChild(lab);
    els.ladder.appendChild(currentDrawEl);
  }
  const bit = ev.result.output === "heads" ? 1 : 0;
  const rung = document.createElement("div");
  rung.className = "rung";
  rung.innerHTML =
    `<span class="n">Flip ${rungInDraw + 1}</span><span class="o">${ev.result.output}</span>` +
    `<span class="b${bit === 1 ? " one" : ""}">${bit}</span>` +
    `<span class="j">${ev.job_id.slice(0, 8)} · ibm ${(ev.result.ibm_job_id || "").slice(0, 16)}</span>`;
  currentDrawEl.appendChild(rung);
  requestAnimationFrame(() => rung.classList.add("in"));
  rungInDraw++;
  if (rungInDraw === 4) {
    rungInDraw = 0;
    drawIndex++;
  }
}

function addDsum(el, bits, idx, accepted, face) {
  const dsum = document.createElement("div");
  dsum.className = "dsum";
  const bitsStr = bits.join(" ");
  dsum.innerHTML = accepted
    ? `<span class="bits">${bitsStr}</span> is ${idx}. Counting from zero, that is <span class="good">side ${face}</span>.`
    : `<span class="bits">${bitsStr}</span> is ${idx}. Only 12 sides, so it goes and we draw again.`;
  el.appendChild(dsum);
}

// The authoritative, retroactive pass (server's own bits, at spin_face_picked)
// — idempotent, skips any draw that already got its explanation live (see
// addDsum's live call site in the quantum_bit case below), so this only
// fills in a gap if the live path somehow missed one, never duplicates it.
function finalizeDraws(bits, face) {
  const draws = els.ladder.querySelectorAll(".draw");
  bits.forEach((draw, i) => {
    const el = draws[i];
    if (!el || el.querySelector(".dsum")) return;
    addDsum(el, draw.bits, draw.idx, draw.accepted, face);
  });
}

/* ---- status (the five-plus states, docs/06-copy.md) ------------------ */
function setStatus(line1html, line2, line3) {
  els.stageLine.innerHTML = line1html;
  els.pollLine.textContent = line2 || "";
  els.clockLine.textContent = line3 || "";
}

function startClock() {
  spinClockStart = performance.now();
  clearInterval(spinClockTimer);
  spinClockTimer = setInterval(() => {
    els.clockLine.textContent = `whole spin ${((performance.now() - spinClockStart) / 1000).toFixed(1)}s`;
  }, 100);
}
function stopClock() {
  clearInterval(spinClockTimer);
}

const ERROR_COPY = {
  // docs/TASKS-site-copy.md §3's three untested states. Nothing has failed
  // in 473 jobs, so none of this has ever actually rendered. The new spec
  // only names these three (an out-of-balance state existed in the old
  // 06-copy.md doc but isn't in this one) — that backend `kind` now falls
  // through to job_failed's generic text below rather than inventing
  // unspecified wording of my own.
  job_failed: ["That flip did not come back. Trying again.", ""],
  unreachable: ["Cannot reach Atlas. Showing the sides as they were.", ""],
};

/* ---- face panel ------------------------------------------------------ */
function renderEmptyFacePanel() {
  // docs/TASKS-site-copy.md §3: a fresh install / before the overnight
  // bake has landed shouldn't show zeroes and a blank image.
  els.facename.textContent = "";
  els.faceversion.textContent = "";
  els.facesub.textContent = "Twelve sides, made before anyone arrived. Press the button to change one.";
  els.faceimg.removeAttribute("src");
  els.faceimg.alt = "";
  if (els.facecredit) els.facecredit.textContent = "";
  els.facerows.innerHTML = "";
  els.vlist.innerHTML = "";
  if (els.maskToggle) els.maskToggle.hidden = true;
}

function renderFacePanel(face, versionEntry, versionList) {
  currentFace = face;
  const v = versionEntry;
  const total = versionList.length;
  els.facename.textContent = `Side ${face}`;
  els.faceversion.textContent = `version ${v.v} of ${total}`;
  els.facesub.textContent = METHOD[v.method] || v.method;
  els.faceimg.src = `/static/faces/${v.file}`;
  els.faceimg.alt = `Side ${face}, version ${v.v}`;
  if (els.facecredit) els.facecredit.textContent = creditLine(face);

  // M3.5: past versions can show the mask that made them, on demand — a
  // toggle, not a second permanent image, since #faceimg only ever holds
  // one src at a time.
  if (els.maskToggle) {
    if (v.mask_file) {
      els.maskToggle.hidden = false;
      els.maskToggle.textContent = "Show mask";
      els.maskToggle.onclick = () => {
        const showingMask = els.faceimg.src.includes(v.mask_file);
        els.faceimg.src = `/static/faces/${showingMask ? v.file : v.mask_file}`;
        els.maskToggle.textContent = showingMask ? "Show mask" : "Show picture";
      };
    } else {
      els.maskToggle.hidden = true;
    }
  }

  els.facerows.innerHTML = "";
  ROWS.forEach(([label, field, get, isCode, getCredit]) => {
    const row = document.createElement("div");
    row.className = "r";
    const value = get(v, face);
    row.innerHTML = `<span class="k">${label}<em>${field}</em></span><span class="v${isCode ? " c" : ""}"></span>`;
    const vEl = row.querySelector(".v");
    vEl.appendChild(document.createTextNode(String(value)));
    const credit = getCredit ? getCredit(v, face) : null;
    if (credit) {
      const em = document.createElement("em");
      em.textContent = `original image: ${credit}`;
      vEl.appendChild(em);
    }
    els.facerows.appendChild(row);
  });

  els.vlist.innerHTML = "";
  versionList.forEach(entry => {
    const row = document.createElement("div");
    row.className = "vrow" + (entry.v === v.v ? " now" : "");
    const when = entry.ts ? new Date(entry.ts).toLocaleString("en-GB", { day: "2-digit", month: "short", hour: "2-digit", minute: "2-digit", hour12: false }) : "overnight batch";
    row.innerHTML =
      `<span class="vthumb" style="background-image:url('/static/faces/${entry.file}')"></span>` +
      `<span class="vmain"><b>Version ${entry.v}, ${entry.method}</b><em>${entry.job_id.slice(0, 16)}</em></span>` +
      `<span class="vfloor">${entry.floor != null ? entry.floor.toFixed(2) : ""}</span>` +
      `<span class="vtime">${when}${entry.elapsed_s != null ? "<br>" + entry.elapsed_s + "s" : ""}</span>`;
    row.addEventListener("click", () => renderFacePanel(face, entry, versionList));
    els.vlist.appendChild(row);
  });
}

async function refreshFacePanel(face) {
  const r = await fetch("/state");
  latestState = await r.json();
  const versionList = latestState.versions[String(face)] || [];
  if (versionList.length) renderFacePanel(face, versionList[versionList.length - 1], versionList);
  else renderEmptyFacePanel();
  return versionList.length;
}

function onFaceSelected(face) {
  frontFace = face;
  setFrontCell(face); // M5: the strip's highlight follows drag/click too, not just spins
  // Clicking/dragging a face to the front shows its picture and data —
  // uses the already-fetched /state data, no network call needed. On the
  // very first, construction-time call, latestState isn't fetched yet —
  // hydrate() picks up frontFace once it lands instead.
  if (!latestState) return;
  const versionList = latestState.versions[String(face)] || [];
  if (versionList.length) renderFacePanel(face, versionList[versionList.length - 1], versionList);
  else renderEmptyFacePanel();
}

/* ---- floor strip under the solid (docs/mask-tasks M5) ----------------- */
function buildFloorStrip() {
  if (!els.floorstrip) return;
  els.floorstrip.innerHTML = "";
  for (let n = 1; n <= 12; n++) {
    const cell = document.createElement("div");
    cell.className = "fcell";
    cell.innerHTML = `<div class="ffill"><i></i></div><span class="fnum">${n}</span>`;
    els.floorstrip.appendChild(cell);
    floorCells[n] = cell;
    floorFills[n] = cell.querySelector("i");
  }
}
buildFloorStrip();

function setFloorFill(face, floor) {
  const i = floorFills[face];
  if (i) i.style.width = `${Math.max(0, Math.min(1, floor)) * 100}%`;
}

function setFrontCell(face) {
  Object.values(floorCells).forEach(c => c.classList.remove("front"));
  if (floorCells[face]) floorCells[face].classList.add("front");
}

/* ---- the live event switch -------------------------------------------- */
function renderEvent(ev) {
  logRow(ev);
  switch (ev.type) {
    case "spin_start":
      clearLadder();
      startClock();
      pickingFace = true;
      // A real bug this exposed: auto-spin drift kept running for the
      // entire multi-second wait (nothing stopped it until snapTo at the
      // very end), and every drift-triggered front-face change fired
      // onFaceSelected, silently overwriting the mask preview and panel
      // with whatever random face happened to be fronting — confirmed
      // directly (a spin landed on face 1, the displayed image ended up
      // being a different face's photo). The whole live sequence — mask
      // preview, ladder, result — is about one specific face; ambient
      // drift has no business competing with it while it's in progress.
      dodeca.setAutoSpin(false);
      currentDrawBits = [];
      setStatus("Working out which side you get.", "Four flips decide which one. About 3.6 seconds each.", "");
      break;
    case "submit":
      break; // no counter tracks this anymore — docs/TASKS-site-copy.md §3
    case "quantum_bit":
      counters.flips++;
      bumpCounters();
      if (pickingFace) {
        landRung(ev);
        setStatus(`Working out which side you get. Flip ${rungInDraw === 0 ? 4 : rungInDraw} of 4.`, `came back ${ev.result.output}`, "");
        currentDrawBits.push(ev.result.output === "heads" ? 1 : 0);
        if (currentDrawBits.length === 4) {
          const bits = currentDrawBits;
          const idx = bits[0] * 8 + bits[1] * 4 + bits[2] * 2 + bits[3];
          currentDrawBits = [];
          if (idx > 11) {
            // Live, not retroactive: this is what was missing — a rejection
            // used to only get explained once the whole spin finished
            // (finalizeDraws, all at once), so watching it happen live gave
            // no reason for why another "go" was starting. Now it writes
            // straight into the ladder, which stays on screen (unlike the
            // status line, which the next draw's own flips overwrite within
            // a few seconds).
            addDsum(currentDrawEl, bits, idx, false, null);
            setStatus(`That is ${idx}. Only 12 sides, so it goes and we draw again.`, "", "");
          }
        }
      }
      break;
    case "spin_face_picked": {
      pickingFace = false;
      // The picked face needs to show up where you're actually looking,
      // immediately — not just in the status text. Turn the solid to it
      // and show its current data in the panel now, before the mask
      // preview and the real photo each arrive later and replace it.
      dodeca.snapTo(ev.face);
      onFaceSelected(ev.face);
      finalizeDraws(ev.bits, ev.face);
      const flips = ev.bits.reduce((n, d) => n + d.bits.length, 0);
      const discarded = ev.bits.filter(d => !d.accepted).length;
      const discardedWord = discarded === 0 ? "none" : discarded === 1 ? "one" : discarded;
      setStatus(
        `Side <span class="hl">${ev.face}</span> is yours. Making the new version now.`,
        `${flips} flips, ${discardedWord} go${discarded === 1 ? "" : "es"} thrown away.`,
        ""
      );
      break;
    }
    case "spin_method_picked":
      // already covered by the "Mixing the two photos" status set above; log row is enough here.
      break;
    case "spin_mask_ready":
      // docs/mask-tasks M3.1-M3.3: the mask fills the 7s wait instead of dead air.
      els.faceimg.src = `/static/faces/${ev.mask_file}`;
      els.faceimg.alt = `Side ${ev.face}, mask preview`;
      els.facesub.innerHTML = `the pale areas are where the new picture comes through <span class="mfloor">floor ${ev.floor.toFixed(2)}</span>`;
      break;
    case "spin_error": {
      stopClock();
      const [l1, l2] = ERROR_COPY[ev.kind] || ERROR_COPY.job_failed;
      setStatus(l1, l2, "");
      els.spinBtn.disabled = false;
      break;
    }
    case "spin_result": {
      stopClock();
      counters.spins++;
      counters.versions++; // a press always rebakes now — see LEARNINGS.md M1
      bumpCounters();
      const imageUrl = `/static/faces/face${String(ev.face).padStart(2, "0")}.jpg?v=${ev.job_id}`;
      dodeca.setFaceImage(ev.face, imageUrl);
      dodeca.snapTo(ev.face);
      refreshFacePanel(ev.face).then(versionCount => {
        setStatus(
          `Side <span class="hl">${ev.face}</span> has changed. Version ${versionCount}, and nobody knew it would be side ${ev.face}.`,
          `It stays that way for whoever comes next. Took ${ev.elapsed_s != null ? ev.elapsed_s + "s" : "—"}, job ${ev.job_id.slice(0, 8)}.`,
          ""
        );
      });
      els.spinBtn.disabled = false;
      break;
    }
    case "floor_stepped":
      // docs/mask-tasks M5.2: updates for everyone watching, the instant a
      // floor commits — before spin_mask_ready, before spin_result, and
      // correct even if the job later errors.
      setFloorFill(ev.face, ev.floor);
      break;
    case "reset":
      break;
    default:
      break;
  }
}

/* ---- hydration on load, then live via SSE ----------------------------- */
async function hydrate() {
  const r = await fetch("/state");
  latestState = await r.json();
  counters = { ...latestState.counters };
  bumpCounters();

  // No dodeca.home() here — that would call snapTo, which stops autoSpin,
  // contradicting "start with the light spin" (item 4). Whatever face
  // naturally fronted at construction (frontFace) is what we show.
  const versionList = latestState.versions[String(frontFace)] || [];
  if (versionList.length) renderFacePanel(frontFace, versionList[versionList.length - 1], versionList);
  else renderEmptyFacePanel();
  Object.keys(latestState.versions).forEach(n => {
    const list = latestState.versions[n];
    if (list.length) dodeca.setFaceImage(parseInt(n, 10), `/static/faces/${list[list.length - 1].file}`);
  });

  // M5: seed the floor strip from each face's latest known floor — no new
  // endpoint, /state's existing versions payload already has it.
  for (let n = 1; n <= 12; n++) {
    const list = latestState.versions[String(n)] || [];
    setFloorFill(n, list.length ? (list[list.length - 1].floor ?? 0) : 0);
  }
  setFrontCell(frontFace);

  setStatus("Press the button and one side changes.", "Four flips decide which one. About 3.6 seconds each.", "");

  const logR = await fetch("/api/log?since=0");
  const logData = await logR.json();
  logData.events.forEach(logRow); // history into the log only, not the ladder/status
}

function connectStream() {
  const es = new EventSource("/stream");
  es.onmessage = e => {
    if (e.data.startsWith(":")) return;
    renderEvent(JSON.parse(e.data));
  };
  es.onerror = () => {
    es.close();
    // Refresh the whole panel, not just counters — a fallback that only
    // ticks numbers up leaves the screen frozen on stale "Flipping..."
    // status if the drop happens mid-spin (observed directly: a real spin
    // completed correctly server-side while a test browser's EventSource
    // had silently fallen back, and only the counters ever moved).
    setInterval(async () => {
      const r = await fetch("/state");
      latestState = await r.json();
      counters = { ...latestState.counters };
      bumpCounters();
      const versionList = latestState.versions[String(frontFace)] || [];
      if (versionList.length) renderFacePanel(frontFace, versionList[versionList.length - 1], versionList);
      else renderEmptyFacePanel();
      for (let n = 1; n <= 12; n++) {
        const list = latestState.versions[String(n)] || [];
        setFloorFill(n, list.length ? (list[list.length - 1].floor ?? 0) : 0);
      }
    }, 2000);
  };
}

function updateAutoSpinBtn() {
  els.autoSpinBtn.textContent = dodeca.isAutoSpin() ? "Stop auto spin" : "Start auto spin";
}
els.autoSpinBtn.addEventListener("click", () => {
  dodeca.setAutoSpin(!dodeca.isAutoSpin());
  updateAutoSpinBtn();
});
updateAutoSpinBtn();
// dodeca.js itself flips autoSpin off on a click-to-select or a landed spin
// result — poll the button label back in sync on the next tick after either.
setInterval(updateAutoSpinBtn, 1000);

/* ---- intro toggle (docs/TASKS-site-copy.md §2) ------------------------ */
function setIntroCollapsed(collapsed) {
  els.intro.classList.toggle("collapsed", collapsed);
  els.introToggle.textContent = collapsed ? "What is this" : "Hide";
  els.introToggle.setAttribute("aria-expanded", String(!collapsed));
}
(function initIntro() {
  let stored = null;
  try {
    stored = localStorage.getItem("introCollapsed");
  } catch (e) { /* private mode / blocked storage — fall through to the default */ }
  const collapsed = stored !== null ? stored === "1" : window.innerWidth < 760;
  setIntroCollapsed(collapsed);
})();
els.introToggle.addEventListener("click", () => {
  const collapsed = !els.intro.classList.contains("collapsed");
  setIntroCollapsed(collapsed);
  try {
    localStorage.setItem("introCollapsed", collapsed ? "1" : "0");
  } catch (e) { /* private mode / blocked storage — the choice just won't persist */ }
});

els.spinBtn.addEventListener("click", async () => {
  if (els.spinBtn.disabled) return;
  els.spinBtn.disabled = true;
  const r = await fetch("/api/spin", { method: "POST" });
  if (r.status === 409) {
    // Someone else's spin is already running (server rejects, doesn't
    // queue — one shared object, everyone watches the same one live).
    // Stays disabled: the in-flight spin's own spin_result/spin_error,
    // which every connected browser receives via /stream, re-enables it.
    setStatus("Someone is changing a side right now. You are next.", "", "");
    return;
  }
  // everything from here plays out live via /stream's renderEvent
});

hydrate().then(connectStream);
