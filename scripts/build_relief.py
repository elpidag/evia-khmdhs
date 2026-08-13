# -*- coding: utf-8 -*-
"""Bake the shaded-relief base for the Atlas fires map.

Pipeline (DATA_DECISIONS 2026-08-13): Copernicus GLO-30 COG tiles read
keyless over /vsicurl at decimated resolution -> mosaic (cached under
data/processed/relief_cache/, gitignored) -> warp to EPSG:3857 grids that
match the d3 map frame EXACTLY (atlas/static/geo/frame.json, emitted by
build-topo.mjs from the same fitSize call PaperMap uses; d3 geoMercator
is EPSG:3857 up to an affine, so the raster registers as one axis-aligned
<image>) -> Patterson resolution-bumping -> multidirectional hillshade
(vendored RVT, Apache-2.0) + sky-view-factor AO + Leland-Brown texture
shading (fractional-Laplacian FFT, public-domain algorithm) -> Huffman
composite -> newsprint tint with a contrast floor so the maroon burn
scars stay the loudest layer -> AVIF x2:

  atlas/static/geo/relief.avif     1280x1240  (always loaded)
  atlas/static/geo/relief_hi.avif  3584x3472  (k>=2 trigger, never narrow;
                                   12.4 MP — desktop/tablet only, phones
                                   are excluded by the narrow flag)

Attribution shipped with the map (mandatory): «Relief: produced using
Copernicus WorldDEM-30 © DLR e.V. 2010-2014 and © Airbus Defence and
Space GmbH 2014-2018 provided under COPERNICUS by the European Union and
ESA; all rights reserved».

Run with SYSTEM python3 (rasterio + numpy + scipy + Pillow with AVIF):
    python3 scripts/build_relief.py [--refetch]
"""
import json
import math
import sys
from pathlib import Path

import numpy as np
import rasterio
from rasterio.merge import merge as rio_merge
from rasterio.transform import from_bounds
from rasterio.warp import Resampling, reproject
from scipy import fft as sfft
from scipy.ndimage import gaussian_filter
from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts/vendor"))
import rvt_vis  # noqa: E402  (vendored, Apache-2.0)

FRAME = ROOT / "atlas/static/geo/frame.json"
CACHE = ROOT / "data/processed/relief_cache"
OUT_LO = ROOT / "atlas/static/geo/relief.avif"
OUT_HI = ROOT / "atlas/static/geo/relief_hi.avif"

BUCKET = "https://copernicus-dem-30m.s3.amazonaws.com"

# ---- the look knobs (tune with the PNG previews in the cache dir) ----
SMOOTH_SIGMA = 1.1        # px on the hi grid (light generalization only)
SMOOTH_KEEP = 0.40        # share of the ORIGINAL detail kept
SUN_ELEV = 35             # multidirectional sun altitude
N_DIR = 16
VE = 3.2                  # vertical exaggeration for the hillshade
SVF_R_MAX = 10            # sky-view-factor radius (px)
AO_WEIGHT = 0.30          # how much the SVF term darkens hollows
TEX_ALPHA = 0.55          # fractional-Laplacian order (texture shading)
TEX_WEIGHT = 0.28         # overlay strength of the texture shade
TEX_FLATS = 0.22          # EXTRA texture weight in the flats — the faint
                          # drainage etching the reference shows in lowlands
GRAIN_AMP = 0.011         # film grain (std of the luminance noise);
GRAIN_SEED = 16849        # deterministic — the bake stays reproducible
SUN_AZ = 300              # primary light direction (WNW, as the reference)
AZ_FOCUS = 2.4            # von-Mises weight: 0 = uniform, higher = directional
SHADOW_STRENGTH = 2.4     # how hard shadow-side slopes darken (pre-floor)
DARK_FLOOR = 0.18         # darkest luminance the relief may reach (0..1)
HIGH_CAP = 0.88           # brightest LAND tone — flats sit AT the plate grey
TONE_GAMMA = 1.4          # >1 rolls midtones smoothly into the shadows
BG_BASE = 0.885           # the background plate (sea) luminance — flats match
GRAD_AMP = 0.045          # global sun gradient across the plate (NW bright,
                          # SE dim — mimics the area light of a 3D render)
CONTACT_AMP = 0.06        # soft contact shadow where the landmass meets the
CONTACT_R = 5.0           # water (px falloff) — the plate reads as physical
HYPSO_WEIGHT = 0.0        # reference look: form from shadows, not elevation tone
# cast shadows (the 3D ingredient): horizon-scan along SUN_AZ with a
# multi-altitude penumbra; shadows fall across the sea like the reference
CAST_ALTS = (16, 21, 26, 31, 36)  # sun altitudes averaged -> soft penumbra
CAST_VE = 3.8             # exaggeration for the shadow caster
CAST_DARK = 0.85          # max darkening from a full cast shadow
CAST_H_FLOOR = 0.25       # shadow weight of a sea-level caster (0..1) —
                          # higher peaks cast proportionally darker shadows
SHADOW_RGB = (0x42, 0x44, 0x4a)   # charcoal shadow anchor — this is
                                  # the darkest colour any shadow can
                                  # reach (the tint ramp's floor)
AVIF_Q = 68

R_MERC = 6378137.0


def merc(lon: float, lat: float) -> tuple[float, float]:
    x = R_MERC * math.radians(lon)
    y = R_MERC * math.log(math.tan(math.pi / 4 + math.radians(lat) / 2))
    return x, y


def fetch_mosaic(bounds4326, res_deg: float, refetch: bool) -> Path:
    """Mosaic the GLO-30 tiles covering bounds into a cached GTiff."""
    CACHE.mkdir(parents=True, exist_ok=True)
    out = CACHE / f"glo30_{res_deg:.5f}.tif"
    if out.exists() and not refetch:
        print(f"mosaic cached: {out.name}")
        return out
    w, s, e, n = bounds4326
    datasets = []
    for lat in range(math.floor(s), math.ceil(n)):
        for lon in range(math.floor(w), math.ceil(e)):
            name = f"Copernicus_DSM_COG_10_N{lat:02d}_00_E{lon:03d}_00_DEM"
            url = f"/vsicurl/{BUCKET}/{name}/{name}.tif"
            try:
                datasets.append(rasterio.open(url))
            except rasterio.errors.RasterioIOError:
                continue  # sea tile, does not exist
    print(f"{len(datasets)} GLO-30 tiles")
    mosaic, transform = rio_merge(datasets, bounds=(w, s, e, n),
                                  res=res_deg, resampling=Resampling.average)
    for d in datasets:
        d.close()
    data = mosaic[0]
    with rasterio.open(
            out, "w", driver="GTiff", width=data.shape[1],
            height=data.shape[0], count=1, dtype="float32", crs="EPSG:4326",
            transform=transform, compress="deflate") as dst:
        dst.write(data.astype("float32"), 1)
    print(f"mosaic: {data.shape[1]}x{data.shape[0]} -> {out.name}")
    return out


def warp_to_frame(mosaic: Path, frame: dict, w: int, h: int) -> np.ndarray:
    """Reproject the 4326 mosaic onto the exact 3857 frame grid."""
    nw_x, nw_y = merc(*frame["nw"])
    se_x, se_y = merc(*frame["se"])
    dst_transform = from_bounds(nw_x, se_y, se_x, nw_y, w, h)
    dst = np.zeros((h, w), dtype="float32")
    with rasterio.open(mosaic) as src:
        reproject(
            source=rasterio.band(src, 1), destination=dst,
            dst_transform=dst_transform, dst_crs="EPSG:3857",
            resampling=Resampling.bilinear)
    return np.maximum(dst, 0.0)


def texture_shade(dem: np.ndarray, alpha: float) -> np.ndarray:
    """Leland Brown fractional-Laplacian texture shading (|f|^alpha in the
    frequency domain). Public-domain algorithm; scipy FFT implementation."""
    h, w = dem.shape
    fh, fw = sfft.next_fast_len(h), sfft.next_fast_len(w)
    F = sfft.rfft2(dem, s=(fh, fw))
    fy = sfft.fftfreq(fh)[:, None]
    fx = sfft.rfftfreq(fw)[None, :]
    H = (np.hypot(fy, fx)) ** alpha
    tex = sfft.irfft2(F * H, s=(fh, fw))[:h, :w]
    lo, hi = np.percentile(tex, [1, 99])
    return np.clip((tex - lo) / (hi - lo), 0, 1)


def cast_shadows(dem: np.ndarray, px_m: float) -> np.ndarray:
    """Soft cast shadows via a horizon scan: rotate so light comes from the
    left, sweep a descending ray height per row, average over several sun
    altitudes for penumbra. Returns shadow intensity 0..1 (1 = full shade).
    Sea is elevation 0, so mountain shadows spill across the water like a
    physical model — the reference's key 3D cue."""
    from scipy.ndimage import rotate as nd_rotate
    angle = 270 - SUN_AZ          # rotate light direction onto -x axis
    z = nd_rotate(dem * CAST_VE, angle, reshape=True, order=1,
                  mode="nearest", cval=0.0)
    # caster-height weighting: the peak that owns the shadow ray decides
    # how dark its shadow is — tall terrain throws deep shadows, hills
    # only faint ones (user ruling 2026-08-13)
    z_ref = max(float(np.percentile(z[z > 0], 97)), 1.0)
    acc = np.zeros_like(z)
    for alt in CAST_ALTS:
        drop = math.tan(math.radians(alt)) * px_m
        ray = np.full(z.shape[0], -np.inf)
        caster = np.zeros(z.shape[0])
        sh = np.zeros_like(z)
        for j in range(z.shape[1]):
            col = z[:, j]
            takeover = col >= ray - drop
            ray = np.maximum(ray - drop, col)
            caster = np.where(takeover, col, caster)
            depth = np.clip((ray - col) / 400.0, 0, 1)
            hw = CAST_H_FLOOR + (1 - CAST_H_FLOOR) * np.clip(caster / z_ref, 0, 1)
            sh[:, j] = depth * hw
        acc += sh
    acc /= len(CAST_ALTS)
    back = nd_rotate(acc, -angle, reshape=True, order=1,
                     mode="nearest", cval=0.0)
    # crop the reshape padding back to the original grid
    dy = (back.shape[0] - dem.shape[0]) // 2
    dx = (back.shape[1] - dem.shape[1]) // 2
    out = back[dy:dy + dem.shape[0], dx:dx + dem.shape[1]]
    return gaussian_filter(np.clip(out, 0, 1), 1.2)


def overlay(base: np.ndarray, top: np.ndarray, k: float) -> np.ndarray:
    """Photoshop overlay blend at strength k."""
    blended = np.where(base < 0.5, 2 * base * top, 1 - 2 * (1 - base) * (1 - top))
    return base * (1 - k) + blended * k


def shade(dem: np.ndarray, px_m: float) -> np.ndarray:
    """The pluggable shade step -> luminance 0..1 (1 = full light).
    A future Blender path replaces exactly this function."""
    # RVT trims a 1px border (it expects pre-padded input) — pad with edge
    # values so every output matches the frame grid exactly
    padded = np.pad(dem, 1, mode="edge")
    mhs = rvt_vis.multi_hillshade(
        padded, resolution_x=px_m, resolution_y=px_m,
        nr_directions=N_DIR, sun_elevation=SUN_ELEV, ve_factor=VE)
    # weighted multidirectional: a uniform mean symmetrizes the light and
    # flattens the relief — weight the directions around SUN_AZ instead
    # (soft von-Mises), keeping multidirectional gentleness with a
    # readable NW raking-light character
    az = np.linspace(0, 360, N_DIR, endpoint=False)
    wgt = np.exp(AZ_FOCUS * np.cos(np.radians(az - SUN_AZ)))
    wgt /= wgt.sum()
    base = np.tensordot(wgt, np.nan_to_num(mhs, nan=1.0), axes=1)
    assert base.shape == dem.shape, (base.shape, dem.shape)
    base = np.clip(base, 0, 1)

    svf = rvt_vis.sky_view_factor(
        dem, resolution=px_m, compute_svf=True, compute_asvf=False,
        compute_opns=False, svf_n_dir=16, svf_r_max=SVF_R_MAX,
        svf_noise=0, ve_factor=VE)["svf"]
    if svf.shape != dem.shape:
        svf = np.pad(svf, ((0, dem.shape[0] - svf.shape[0]),
                           (0, dem.shape[1] - svf.shape[1])), mode="edge")
    svf = np.clip(np.nan_to_num(svf, nan=1.0), 0, 1)
    out = base * (1 - AO_WEIGHT + AO_WEIGHT * svf)

    tex = texture_shade(dem, TEX_ALPHA)
    tex[dem <= 0] = 0.5          # neutral over sea — the land/sea step rings
    # flats get extra texture: where the multidirectional shade sits near
    # its flat-ground value, the drainage etching carries the form
    flat_v = math.sin(math.radians(SUN_ELEV))
    flatness = np.clip(1.0 - np.abs(base - flat_v) / 0.12, 0, 1)
    k = TEX_WEIGHT + TEX_FLATS * flatness
    return np.clip(overlay(out, tex, k), 0, 1)


def to_luminance(shade_v: np.ndarray) -> np.ndarray:
    """Huffman-style remap: a hillshade values FLAT ground at
    sin(sun_elevation) — mapping that straight to grey turns the whole
    landmass into a silhouette. Instead plains stay paper-white and only
    shadow-side slopes darken (linear-burn spirit); sun-side slopes stay
    at paper (the paper IS the highlight)."""
    flat = math.sin(math.radians(SUN_ELEV))
    shadow = np.clip((flat - shade_v) / flat, 0, 1)
    # soft compression into [DARK_FLOOR, HIGH_CAP] with a gamma roll-off —
    # the geoblender reference: no pure white on land, midtones melting
    # smoothly into the shadows
    lum = np.clip(1.0 - SHADOW_STRENGTH * shadow, 0, 1) ** TONE_GAMMA
    return DARK_FLOOR + (HIGH_CAP - DARK_FLOOR) * lum


def sun_gradient(shape: tuple[int, int]) -> np.ndarray:
    """Global illumination ramp along the sun axis: the corner facing
    SUN_AZ is brightest, the far corner dimmest — the whole plate reads
    as lit by one big area light (the 3D-render cue)."""
    h, w = shape
    yy, xx = np.mgrid[0:h, 0:w]
    az = math.radians(SUN_AZ)
    # unit vector pointing TOWARD the sun in image coords (x east, y south)
    ux, uy = math.sin(az), -math.cos(az)
    t = (xx / (w - 1) - 0.5) * ux + (yy / (h - 1) - 0.5) * uy
    t = t / (abs(t).max() or 1.0)
    return 1.0 + GRAD_AMP * t


def tint(lum: np.ndarray, sea: np.ndarray, shadow: np.ndarray) -> Image.Image:
    """One neutral charcoal->white ramp for everything (geoblender look):
    the sea is the background plate at BG_BASE, flats sit at HIGH_CAP just
    under it, cast shadows grey the water they cross, a soft contact
    shadow hugs the coast, and the sun gradient lights the whole plate."""
    from scipy.ndimage import distance_transform_edt
    lum = np.clip(lum, 0, 1)
    sea_lum = BG_BASE * np.clip(1.0 - CAST_DARK * shadow, 0, 1)
    d = distance_transform_edt(sea)
    contact = 1.0 - CONTACT_AMP * np.exp(-d / CONTACT_R)
    sea_lum = sea_lum * contact
    final = np.where(sea, sea_lum, lum) * sun_gradient(lum.shape)
    # film grain over the whole plate (a render's sensor noise) —
    # deterministic so the bake is reproducible
    rng = np.random.default_rng(GRAIN_SEED)
    final = final + rng.normal(0.0, GRAIN_AMP, final.shape)
    final = np.clip(final, 0, 1)
    rgb = np.empty((*final.shape, 3), dtype="float32")
    for c, sc in enumerate(SHADOW_RGB):
        rgb[..., c] = sc + (255 - sc) * final
    return Image.fromarray(np.clip(rgb, 0, 255).astype("uint8"))


def build(frame: dict, mosaic: Path, w: int, h: int, out: Path) -> None:
    dem = warp_to_frame(mosaic, frame, w, h)
    # coastline hygiene: resampling leaves sub-metre partial-land pixels
    # along coasts (stippled fringe) and isolated specks in open sea (fake
    # micro-islands) — threshold at 1 m and drop land components < 8 px
    from scipy.ndimage import label
    sea = dem < 1.0
    lab, n = label(~sea)
    if n:
        sizes = np.bincount(lab.ravel())
        small = np.isin(lab, np.nonzero(sizes < 8)[0][1:] if sizes.size > 1
                        else [])
        sea |= small
    dem[sea] = 0
    smooth = gaussian_filter(dem, SMOOTH_SIGMA)
    dem_g = smooth * (1 - SMOOTH_KEEP) + dem * SMOOTH_KEEP
    nw_x, _ = merc(*frame["nw"])
    se_x, _ = merc(*frame["se"])
    px_m = (se_x - nw_x) / w
    lum = to_luminance(shade(dem_g, px_m))
    shadow = cast_shadows(dem_g, px_m)
    lum = np.clip(lum * (1.0 - CAST_DARK * shadow), 0, 1)
    lum = gaussian_filter(lum, 0.5)      # velvet: soften the shade grain
    if HYPSO_WEIGHT:
        hi_ref = max(float(np.percentile(dem_g[~sea], 98)), 1.0)
        lum = np.clip(lum - HYPSO_WEIGHT * np.clip(dem_g / hi_ref, 0, 1), 0, 1)
    img = tint(lum, sea, shadow)
    img.save(out, "AVIF", quality=AVIF_Q)
    preview = CACHE / (out.stem + "_preview.png")
    img.save(preview, "PNG")
    print(f"{out.name}: {w}x{h}, {out.stat().st_size / 1024:.0f} KB "
          f"(preview {preview.name})")


def main() -> None:
    refetch = "--refetch" in sys.argv
    frame = json.loads(FRAME.read_text(encoding="utf-8"))
    lons = sorted([frame["nw"][0], frame["se"][0]])
    lats = sorted([frame["nw"][1], frame["se"][1]])
    span_deg = lons[1] - lons[0]
    res_deg = span_deg / (3584 * 2)          # fetch at 2x the hi grid
    mosaic = fetch_mosaic((lons[0], lats[0], lons[1], lats[1]),
                          res_deg, refetch)
    build(frame, mosaic, 3584, 3472, OUT_HI)
    build(frame, mosaic, 1280, 1240, OUT_LO)


if __name__ == "__main__":
    main()
