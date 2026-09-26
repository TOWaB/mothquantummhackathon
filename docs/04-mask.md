# 04. The mask

Current pipeline: rembg silhouette, then `distance_gradient` with radius 30, then that gradient goes to `telablur-v1` as the mask.

---

## The correction

Radius controls how soft the edge is. It does not control how protected the middle of the person is. Moving radius from 30 to 30.03 changes the feather by three hundredths of a pixel. Push it to 300 and the edge goes hazy but the deepest interior still reads as fully protected, because the distance from there to the silhouette edge is still large.

**`floor` is what makes the person dissolve.** It is the lowest value the mask may take, and it does not exist in the code yet.

```
d       signed distance from the silhouette edge, negative inside the person
erode   pixels to shrink (+) or grow (−) the protected region
radius  width of the soft transition
floor   lowest value the mask may reach, 0 to 1

m = clamp( (d + erode) / radius + 0.5, 0, 1 )
M = floor + (1 - floor) * m
```

| | Effect | Drift parameter |
|---|---|---|
| `radius` | Edge softness | No. Invisible below about 5 percent change |
| `erode` | Eats the person from the outside in. Geometric, reads as dissolving | Secondary |
| `floor` | How much effect reaches the deepest interior | Primary |

`floor = 0` reproduces today's output exactly, which is the regression test for B1.

---

## Python

```python
import numpy as np
from scipy.ndimage import distance_transform_edt

def signed_distance(alpha: np.ndarray) -> np.ndarray:
    """alpha: HxW, True inside the person. Returns signed distance in pixels,
    negative inside, positive outside."""
    inside  = alpha.astype(bool)
    d_out   = distance_transform_edt(~inside)   # distance to the person
    d_in    = distance_transform_edt(inside)    # distance to the background
    return np.where(inside, -d_in, d_out)

def make_mask(alpha, radius=30.0, erode=0.0, floor=0.0) -> np.ndarray:
    """0 protects the pixel completely, 1 lets the effect through completely."""
    d = signed_distance(alpha)
    m = np.clip((d + erode) / radius + 0.5, 0.0, 1.0)
    return floor + (1.0 - floor) * m

def to_png_bytes(mask, path):
    from PIL import Image
    Image.fromarray((mask * 255).astype(np.uint8), mode="L").save(path)
```

Drop-in for the current call site:

```python
# before
mask = distance_gradient(alpha, radius=30)

# after — identical output while floor and erode are zero
mask = make_mask(alpha, radius=30, erode=0.0, floor=floors[face])
```

---

## The drift

`floor` is not a slider. It moves a little on every spin, so the sides people look at are the ones that erode.

```python
import json, pathlib

FLOORS = pathlib.Path("state/floors.json")

def load_floors():
    if FLOORS.exists():
        return json.loads(FLOORS.read_text())
    return {str(n): 0.0 for n in range(1, 13)}

def save_floors(f):
    FLOORS.parent.mkdir(exist_ok=True)
    FLOORS.write_text(json.dumps(f, indent=2))

def reflect(x):
    """Keeps the walk off the walls. A clamped walk parks at 0 or 1 and stays
    there, which is the one state we do not want."""
    if x < 0.0: x = -x
    if x > 1.0: x = 2.0 - x
    return x

def step_floor(face, direction, step=0.02):
    f = load_floors()
    f[str(face)] = reflect(f[str(face)] + direction * step)
    save_floors(f)
    return f[str(face)]
```

`direction` is +1 or −1 and comes from the flips. See `02-quantum-open.md` Q5, which is Aja's to decide.

---

## Sizing the step

A random walk moves `step × √n` after n spins.

| Spins | step 0.001 | step 0.02 |
|---|---|---|
| 50 | 0.007 | 0.14 |
| 200 | 0.014 | 0.28 |
| 500 | 0.022 | 0.45 |

At 0.001 nothing visibly moves all day. 0.02 is the suggested starting point and individual sides go much further than the typical figure.

Settle it by eye in the mask lab rather than from this table.

---

## What to check before building

The `telablur-v1` submit event in `api_log.jsonl` records only `strength` and `direction`. `mask_radius` and `mask_type` appear in `manifest.json` but not in the submit.

If that is right, the mask is generated locally and uploaded as an asset, and `mask_radius` and `mask_type` are our own record of how we made it rather than Atlas parameters. That would mean the whole pipeline is ours with no engine limits, and `floor`, `erode` and the walk go in without touching the API.

Confirm it first. If the engine does take mask parameters, the range it accepts decides the step size.
