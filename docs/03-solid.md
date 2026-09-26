# 03. The solid

Replaces `static/js/dodeca.js`. Copy the code, it works as written.

---

## The trap that broke it first time

**`clip-path` on the element carrying the 3D transform drops it out of the 3D rendering context.** The browser then paints it flat, in document order, with its own transform applied but no depth relationship to its siblings. Twelve pentagons at assorted sizes overlapping in the wrong order.

The same applies to `filter`, `opacity` below 1, `mask`, `overflow` other than visible, `mix-blend-mode` and `contain: paint`.

Fix is one level of nesting.

```html
<div class="pface" style="transform: rotateY() rotateX() translateZ() rotateZ()">
  <div class="pclip"><!-- clip-path, photograph, labels live here --></div>
</div>
```

```css
.pface { position:absolute; inset:0; backface-visibility:hidden; }  /* nothing else */
.pclip { position:absolute; inset:0;
  clip-path: polygon(50% 0%, 97.55% 34.55%, 79.39% 90.45%, 20.61% 90.45%, 2.45% 34.55%);
  background: #0b0b0d center/cover no-repeat; }
```

Any drop shadow or blur added to a face later goes on `.pclip`, never on `.pface`.

---

## Geometry

The twelve face normals are the twelve vertices of an icosahedron. One at the pole, five at 63.435° from it, five at 116.565°, one at the far pole. 63.435° is `arctan(2)`.

```
face box side          S
pentagon circumradius  S / 2          (the clip-path fills the box)
solid inradius         R = 1.30902 × (S / 2) = 0.6545 × S
```

1.30902 is φ²/2.

| Ring | Faces | Azimuth | Elevation | In-plane spin |
|---|---|---|---|---|
| Top | 1 | 0° | 90° | 36° |
| Upper | 5 | 36 + 72i | 26.565° | 36° |
| Lower | 5 | 72i | −26.565° | 0° |
| Bottom | 1 | 0° | −90° | 36° |

A pentagon maps onto itself every 72°, so each ring has only two meaningful spins, 0 and 36. Brute-forcing all sixteen combinations against the vertex positions gives exactly two that close: the table above, and one mirrored version with the upper ring starting at azimuth 0.

**Self-test.** Rebuild all 60 corners, cluster them, and count. A dodecahedron has 20 corners with 3 faces at each. Anything else means the config is wrong. `checkGeometry()` below does this in about 20 lines and is worth keeping in the shipped code.

---

## Why a quaternion and not `rotateX` / `rotateY`

After the first turn, `rotateX` and `rotateY` no longer line up with the screen, so diagonal dragging fights you. One quaternion holds the orientation, is written out as a single `matrix3d`, has no gimbal lock, does not drift across thousands of small turns, and can be interpolated for the snap.

The part that matters is **pre-multiplying**. Post-multiplying applies the turn in the object's own frame, which is the naive version that feels wrong.

```js
const len   = Math.hypot(dx, dy);
const axis  = [-dy / len, dx / len, 0];   // perpendicular to the drag
const angle = len * 0.008;                // radians per pixel
q = qMul(qAxis(axis, angle), q);          // pre-multiply keeps it in screen space
solid.style.transform = qMatrix3d(q);
```

---

## The whole file

```js
/* dodeca.js — 12 pentagon faces, one quaternion, drag / inertia / snap */
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
      if (moved < 6 && performance.now() - downT < 400 && target)
        api.snapTo(+target.dataset.face);
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
      } else if (!dragging && !reduce && t - lastInput > 2800) {
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
      },
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
```

---

## Using it

```js
const solid = Dodeca(document.getElementById("stage"), {
  size: 200,
  onFace: n => showFace(n)          // fires when a new face comes to the front
});

console.assert(solid.checkGeometry().ok, "dodecahedron does not close");

for (let n = 1; n <= 12; n++)
  solid.setFaceImage(n, `/out/16_dodecahedron_faces/face${String(n).padStart(2,"0")}.png`);

// when a spin picks a side
solid.snapTo(8);
```

Required on `#stage`:

```css
#stage { perspective: 720px; touch-action: none; user-select: none;
         display: grid; place-items: center; overflow: hidden; }
```

`overflow: hidden` is fine on `#stage` because it holds the perspective. It is not fine on `#solid` or on any face.

---

## Why not Three.js

It gives drag, inertia and lighting through OrbitControls. The cost is that `DodecahedronGeometry` is triangulated with UVs that fight pentagon textures, so you build twelve pentagon meshes by hand anyway, then a texture loader, then raycasting for clicks. About 40 lines of quaternion maths against a day and 600 kB.

Take Three.js when the solid needs to look lit. For twelve photographs, lighting fights the images.
