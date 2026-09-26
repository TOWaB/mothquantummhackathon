"""Reusable mask primitives. Every mask-using script should build masks from
these instead of inlining its own rembg/numpy calls (sets 03, 04, 09 each did
their own thing — this replaces that pattern going forward).

All functions take/return single-channel ("L") PIL Images, white=255=full
effect, black=0=protected.
"""
from pathlib import Path

import numpy as np
from PIL import Image, ImageFilter, ImageOps
from rembg import new_session, remove
from scipy.ndimage import distance_transform_edt

# Explicit, deliberately light session — rembg's own unqualified default
# (whatever its current release resolves to; confirmed live tonight,
# 26-09-2026, to be "bria-rmbg", ~1GB on disk) pushed this process to
# ~6.8GB RSS on a 7.7GB shared box, and the kernel OOM-killer took it out
# every single time a spin reached this call — silently, mid-spin, no
# error logged, no telablur-v1 call ever made. u2netp is rembg's own
# "portable" pruned model (~4.7MB): a visibly rougher silhouette, but
# this only ever feeds a distance-transform gradient, not a pixel-perfect
# matte, and a working rough mask beats a process that cannot survive
# calling this function at all.
_SESSION = new_session("u2netp")


def segment_person(image_path: Path) -> Image.Image:
    photo = Image.open(image_path).convert("RGB")
    cutout = remove(photo, session=_SESSION)
    return cutout.split()[-1]  # alpha channel, white=subject


def invert(mask: Image.Image) -> Image.Image:
    return ImageOps.invert(mask.convert("L"))


def feather(mask: Image.Image, radius: float) -> Image.Image:
    return mask.convert("L").filter(ImageFilter.GaussianBlur(radius))


def _odd(px: int) -> int:
    px = max(1, int(px))
    return px if px % 2 == 1 else px + 1


def erode(mask: Image.Image, px: int) -> Image.Image:
    """Shrink the white region by ~px."""
    return mask.convert("L").filter(ImageFilter.MinFilter(_odd(px)))


def dilate(mask: Image.Image, px: int) -> Image.Image:
    """Grow the white region by ~px."""
    return mask.convert("L").filter(ImageFilter.MaxFilter(_odd(px)))


def combine(mask_a: Image.Image, mask_b: Image.Image, op: str = "union") -> Image.Image:
    a = np.array(mask_a.convert("L"), dtype=np.float32)
    b = np.array(mask_b.convert("L"), dtype=np.float32)
    if op == "union":
        out = np.maximum(a, b)
    elif op == "intersect":
        out = np.minimum(a, b)
    elif op == "subtract":
        out = np.clip(a - b, 0, 255)
    else:
        raise ValueError(f"unknown op {op!r} (union/intersect/subtract)")
    return Image.fromarray(out.astype("uint8"), "L")


def lerp(mask_a: Image.Image, mask_b: Image.Image, t: float) -> Image.Image:
    """Blend two masks; t=0 -> mask_a, t=1 -> mask_b."""
    a = np.array(mask_a.convert("L"), dtype=np.float32)
    b = np.array(mask_b.convert("L"), dtype=np.float32)
    out = a * (1 - t) + b * t
    return Image.fromarray(out.astype("uint8"), "L")


def radial_gradient(size: tuple[int, int], center=None, radius=None, invert_falloff=False) -> Image.Image:
    w, h = size
    cx, cy = center or (w / 2, h / 2)
    r = radius or (min(w, h) / 2)
    yy, xx = np.mgrid[0:h, 0:w]
    dist = np.sqrt((xx - cx) ** 2 + (yy - cy) ** 2)
    norm = np.clip(dist / r, 0, 1)
    val = norm if not invert_falloff else 1 - norm
    return Image.fromarray((val * 255).astype("uint8"), "L")


def stripes(size: tuple[int, int], count: int = 8, direction: str = "vertical") -> Image.Image:
    w, h = size
    xx, yy = np.meshgrid(np.arange(w), np.arange(h))
    coord = xx if direction == "vertical" else yy
    span = (w if direction == "vertical" else h) // max(1, count)
    band = ((coord // max(1, span)) % 2) * 255
    return Image.fromarray(band.astype("uint8"), "L")


def full_white(size: tuple[int, int]) -> Image.Image:
    return Image.new("L", size, 255)


def make_mask(alpha_mask: Image.Image, radius: float = 30.0, erode: float = 0.0, floor: float = 0.0) -> Image.Image:
    """distance_gradient plus `erode` (shrinks/grows the protected region) and
    `floor` (the lowest value the mask may reach — 0 protects the deepest
    interior completely, >0 lets some effect reach it, which is what makes a
    person progressively dissolve rather than just having a softer edge).

    Deliberately keeps distance_gradient's own denominator (2*radius, not the
    bare `radius` docs/04-mask.md's formula shows) so that erode=0, floor=0,
    radius=30 is BYTE IDENTICAL to distance_gradient(alpha, radius=30) — the
    regression test 04-mask.md itself specifies for B1. Using the doc's literal
    formula verbatim would halve the effective transition width at the same
    numeric radius and break every already-baked face. See LEARNINGS.md,
    2026-09-26, for why the formula here differs from the doc's own text.
    """
    binary = np.array(alpha_mask.convert("L")) > 127
    dist_inside = distance_transform_edt(binary)
    dist_outside = distance_transform_edt(~binary)
    signed = np.where(binary, dist_inside, -dist_outside)  # + inside, - outside
    m = np.clip(0.5 - (signed - erode) / (2 * radius), 0.0, 1.0)
    val = floor + (1.0 - floor) * m
    return Image.fromarray((val * 255).astype("uint8"), "L")


def ring_overlay(gradient: Image.Image, alpha_mask: Image.Image, color=(240, 242, 46), opacity: float = 0.35) -> Image.Image:
    """A display-only RGB copy of a grayscale mask with a faint ring drawn at
    the silhouette boundary (docs/mask-tasks TASKS-mask.md M3.4). Never feed
    this to Atlas as the masking channel — telablur consumes the raw
    grayscale gradient values as data, and this overlay changes some of
    those values along the ring. Callers upload the plain `gradient` for
    the real job and save *this* only as the servable/stored preview.
    """
    binary = np.array(alpha_mask.convert("L")) > 127
    from scipy.ndimage import binary_erosion
    boundary = binary & ~binary_erosion(binary, iterations=1)
    rgb = np.array(gradient.convert("RGB"), dtype=np.float32)
    ring_color = np.array(color, dtype=np.float32)
    rgb[boundary] = rgb[boundary] * (1 - opacity) + ring_color * opacity
    return Image.fromarray(rgb.astype("uint8"), "RGB")


def distance_gradient(alpha_mask: Image.Image, radius: float = 60, invert: bool = False) -> Image.Image:
    """Shape-aware gradient that follows alpha_mask's own silhouette (not a
    generic circle): 0 (protected) deep inside the shape, 255 (full effect)
    far outside it, with a smooth transition straddling the edge over
    `radius` px. Bigger radius = softer, farther-reaching transition (eats
    more of the shape / bleeds further into the background)."""
    binary = np.array(alpha_mask.convert("L")) > 127
    dist_inside = distance_transform_edt(binary)
    dist_outside = distance_transform_edt(~binary)
    signed = np.where(binary, dist_inside, -dist_outside)  # + = inside, - = outside
    val = np.clip(0.5 - signed / (2 * radius), 0, 1)
    if invert:
        val = 1 - val
    return Image.fromarray((val * 255).astype("uint8"), "L")
