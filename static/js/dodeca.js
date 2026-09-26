/* dodeca.js — 12 pentagon faces, one quaternion, drag / inertia / snap
 * Verbatim from docs/03-solid.md (Track C1) — "copy the code, it works as
 * written." Replaces the earlier per-face-matrix3d version (see
 * LEARNINGS.md, 2026-09-26): that one used rotate3d + translateZ directly
 * on the transformed element with no clip-path trap because it put the
 * clip-path on the SAME element as the 3D transform, which this doc
 * explicitly says drops an element out of the 3D rendering context. It
 * happened to look right by luck (no clip-path was in use yet); this
 * version is the one built to survive that trap on purpose. */
(function (global) {
  "use strict";
  const D = Math.PI / 180;

  /* ---- quaternion ---- */
  const qMul = (a, b) => [
    a[0]*b[0]-a[1]*b[1]-a[2]*b[2]-a[3]*b[3],
    a[0]*b[1]+a[1]*b[0]+a[2]*b[3]-a[3]*b[2],
    a[0]*b[2]-a[1]*b[3]+a[2]*b[0]+a[3]*b[1],
    a[0]*b[3]+a[1]*b[2]-a[2]*b[1]+a[3]*b[0]];
  const qNorm = q => { const n = Math.hypot(...q) || 1; return q.map(v => v / n); };
  const qAxis = (ax, ang) => { const s = Math.sin(ang/2);
    return [Math.cos(ang/2), ax[0]*s, ax[1]*s, ax[2]*s]; };
  const qM = ([w,x,y,z]) => [
    1-2*(y*y+z*z), 2*(x*y-w*z),   2*(x*z+w*y),
    2*(x*y+w*z),   1-2*(x*x+z*z), 2*(y*z-w*x),
    2*(x*z-w*y),   2*(y*z+w*x),   1-2*(x*x+y*y)];
  const qRot = (q, v) => { const m = qM(q); return [
    m[0]*v[0]+m[1]*v[1]+m[2]*v[2],
    m[3]*v[0]+m[4]*v[1]+m[5]*v[2],
    m[6]*v[0]+m[7]*v[1]+m[8]*v[2]]; };
  const qMatrix3d = q => { const m = qM(q);
    return "matrix3d(" + [m[0],m[3],m[6],0, m[1],m[4],m[7],0, m[2],m[5],m[8],0, 0,0,0,1]
      .map(v => v.toFixed(6)).join(",") + ")"; };
  function qSlerp(a, b, t) {
    let d = a[0]*b[0]+a[1]*b[1]+a[2]*b[2]+a[3]*b[3];
    if (d < 0) { b = b.map(v => -v); d = -d; }
    if (d > 0.9995) return qNorm(a.map((v, i) => v + (b[i]-v)*t));
    const th = Math.acos(d), s = Math.sin(th);
    const w1 = Math.sin((1-t)*th)/s, w2 = Math.sin(t*th)/s;
    return a.map((v, i) => v*w1 + b[i]*w2);
  }
  function rotBetween(a, b) {
    const c = [a[1]*b[2]-a[2]*b[1], a[2]*b[0]-a[0]*b[2], a[0]*b[1]-a[1]*b[0]];
    const s = Math.hypot(...c), dot = a[0]*b[0]+a[1]*b[1]+a[2]*b[2];
    if (s < 1e-8) return dot > 0 ? [1,0,0,0] : [0,1,0,0];
    return qAxis(c.map(v => v/s), Math.atan2(s, dot));
  }

  /* ---- geometry ---- */
  function buildSpec() {
    const s = [{ az: 0, el: 90, z: 36, n: 1 }];
    for (let i = 0; i < 5; i++) s.push({ az: 36+72*i, el:  26.565051, z: 36, n: 2+i });
    for (let i = 0; i < 5; i++) s.push({ az: 72*i,    el: -26.565051, z:  0, n: 7+i });
    s.push({ az: 0, el: -90, z: 36, n: 12 });
    return s;
  }
  const normalOf = s => {
    const e = s.el*D, a = s.az*D;
    return [Math.cos(e)*Math.sin(a), -Math.sin(e), Math.cos(e)*Math.cos(a)];
  };

  function Dodeca(stage, opts = {}) {
    const size  = opts.size  || 200;
    const Rp    = size / 2;
    const Rin   = 1.3090169943749475 * Rp;
    const spec  = buildSpec();
    const normals = spec.map(normalOf);

    const solid = document.createElement("div");
    solid.style.cssText =
      `width:${size}px;height:${size}px;position:relative;transform-style:preserve-3d`;
    stage.appendChild(solid);

    const faces = spec.map(s => {
      const f = document.createElement("div");
      f.className = "pface";
      f.dataset.face = s.n;
      f.style.transform =
        `rotateY(${s.az}deg) rotateX(${s.el}deg) translateZ(${Rin.toFixed(2)}px) rotateZ(${s.z}deg)`;
      const c = document.createElement("div");
      c.className = "pclip";
      f.appendChild(c);
      solid.appendChild(f);
      return f;
    });

    let q = qNorm(qMul(qAxis([1,0,0], -0.22), qAxis([0,1,0], 0.42)));
    let vel = null, dragging = false, cur = -1, lastInput = performance.now();
    let slerpFrom = null, slerpTo = null, slerpStart = 0;
    let autoSpin = true; // the light idle drift, on by default; a click or a
                          // landed spin result stops it persistently — see
                          // end() and snapTo() below, not just a paused timer.

    const apply = () => { solid.style.transform = qMatrix3d(q); };
    const front = () => {
      let b = -1, bd = -2;
      normals.forEach((n, i) => { const w = qRot(q, n); if (w[2] > bd) { bd = w[2]; b = i; } });
      return b;
    };
    function mark() {
      const f = front();
      if (f === cur || f < 0) return;
      cur = f;
      faces.forEach((el, i) => el.classList.toggle("sel", i === cur));
      if (opts.onFace) opts.onFace(+faces[cur].dataset.face);
    }

    /* ---- pointer ---- */
    let px = 0, py = 0, downT = 0, moved = 0, target = null;
    stage.addEventListener("pointerdown", e => {
      // UI chrome living inside #stage (the HUD buttons) must be left alone:
      // setPointerCapture below redirects every further pointer event for
      // this pointerId to #stage regardless of where it landed, which
      // silently swallows a real mouse click on a button underneath it.
      // Confirmed directly: a native el.click() worked, a real simulated
      // mouse click did not, until this bailout was added.
      if (e.target.closest && e.target.closest(".hud")) return;
      dragging = true; vel = null; slerpTo = null; moved = 0;
      px = e.clientX; py = e.clientY; downT = performance.now();
      target = e.target.closest ? e.target.closest(".pface") : null;
      stage.setPointerCapture(e.pointerId); lastInput = performance.now();
    });
    stage.addEventListener("pointermove", e => {
      if (!dragging) return;
      const dx = e.clientX - px, dy = e.clientY - py;
      px = e.clientX; py = e.clientY; moved += Math.hypot(dx, dy);
      const len = Math.hypot(dx, dy);
      if (len > 0) {
        const axis = [-dy/len, dx/len, 0], ang = len * 0.008;
        q = qNorm(qMul(qAxis(axis, ang), q));
        vel = { axis, ang };
        apply(); mark();
      }
      lastInput = performance.now();
    });
    const end = () => {
      if (!dragging) return;
      dragging = false;
      if (moved < 6 && performance.now() - downT < 400 && target) {
        api.snapTo(+target.dataset.face);
        autoSpin = false; // a genuine click-to-select stops the drift, not just for a moment
      }
      lastInput = performance.now();
    };
    stage.addEventListener("pointerup", end);
    stage.addEventListener("pointercancel", end);

    /* ---- loop ---- */
    const reduce = matchMedia("(prefers-reduced-motion: reduce)").matches;
    (function frame(t) {
      if (slerpTo) {
        const k = Math.min(1, (t - slerpStart) / 700);
        const e = k < 0.5 ? 4*k*k*k : 1 - Math.pow(-2*k+2, 3)/2;
        q = qSlerp(slerpFrom, slerpTo, e);
        if (k >= 1) slerpTo = null;
        apply(); mark();
      } else if (!dragging && vel) {
        vel.ang *= 0.95;
        if (vel.ang < 0.0006) vel = null;
        else { q = qNorm(qMul(qAxis(vel.axis, vel.ang), q)); apply(); mark(); }
      } else if (!dragging && autoSpin && !reduce) {
        q = qNorm(qMul(qAxis([0,1,0], 0.0018), q)); apply(); mark();
      }
      requestAnimationFrame(frame);
    })(0);

    const api = {
      setFaceImage(n, url) {
        faces[n-1].querySelector(".pclip").style.backgroundImage = `url('${url}')`;
      },
      snapTo(n) {
        const w = qRot(q, normals[n-1]);
        slerpFrom = q.slice();
        slerpTo = qNorm(qMul(rotBetween(w, [0,0,1]), q));
        slerpStart = performance.now(); vel = null;
        autoSpin = false; // a spin result lands and stays, it doesn't drift off again
      },
      setAutoSpin(on) { autoSpin = !!on; },
      isAutoSpin() { return autoSpin; },
      home() { api.snapTo(1); },
      checkGeometry() {
        const Rx = t => { const c = Math.cos(t), s = Math.sin(t); return [1,0,0, 0,c,-s, 0,s,c]; };
        const Ry = t => { const c = Math.cos(t), s = Math.sin(t); return [c,0,s, 0,1,0, -s,0,c]; };
        const Rz = t => { const c = Math.cos(t), s = Math.sin(t); return [c,-s,0, s,c,0, 0,0,1]; };
        const mm = (a,b) => { const o = []; for (let i=0;i<3;i++) for (let j=0;j<3;j++) {
          let s = 0; for (let k=0;k<3;k++) s += a[i*3+k]*b[k*3+j]; o[i*3+j] = s; } return o; };
        const mv = (m,v) => [m[0]*v[0]+m[1]*v[1]+m[2]*v[2],
                             m[3]*v[0]+m[4]*v[1]+m[5]*v[2],
                             m[6]*v[0]+m[7]*v[1]+m[8]*v[2]];
        const pts = [], uniq = [], counts = [];
        spec.forEach(s => {
          const M = mm(Ry(s.az*D), Rx(s.el*D));
          for (let k = 0; k < 5; k++) {
            const a = 72*k*D;
            const v = mv(Rz(s.z*D), [Rp*Math.sin(a), -Rp*Math.cos(a), 0]);
            pts.push(mv(M, [v[0], v[1], v[2] + Rin]));
          }
        });
        pts.forEach(p => {
          for (let i = 0; i < uniq.length; i++) {
            const u = uniq[i];
            if (Math.hypot(p[0]-u[0], p[1]-u[1], p[2]-u[2]) < 1.2) { counts[i]++; return; }
          }
          uniq.push(p); counts.push(1);
        });
        return { corners: uniq.length, facesPerCorner: [...new Set(counts)],
                 ok: uniq.length === 20 && new Set(counts).size === 1 && counts[0] === 3 };
      }
    };
    apply(); mark();
    return api;
  }

  global.Dodeca = Dodeca;
})(window);
