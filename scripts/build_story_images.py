"""Build the story figures' WEB derivatives from the author's originals.

The author uploads full-size material into atlas/static/img/story/ —
Figure<NN><letter?>.png singles and figure01/<NN>_… .png for the Figure 01
grid (DATA_DECISIONS 2026-09-02). Those originals (and the .psd) stay on
disk but are GITIGNORED and never referenced by the site; this script emits
small .webp derivatives next to them, which are committed and served:

    Figure02a.png            -> fig02a.webp            (max 1100 px)
    figure01/01_… .png       -> fig01/01.webp          (max 320 px)

Re-run after the author adds or replaces originals. Requires Pillow.
"""

from pathlib import Path
import re

from PIL import Image

ROOT = Path(__file__).resolve().parent.parent / "atlas" / "static" / "img" / "story"
SINGLE_MAX = 1100  # the slot renders at 540 css px; x2 for dpr
GRID_MAX = 320  # a grid cell is ~143 css px; x2 for dpr
QUALITY = 82


def emit(src: Path, dst: Path, max_px: int) -> None:
    with Image.open(src) as im:
        im = im.convert("RGB")
        im.thumbnail((max_px, max_px), Image.LANCZOS)
        dst.parent.mkdir(parents=True, exist_ok=True)
        im.save(dst, "WEBP", quality=QUALITY, method=6)
    print(f"{dst.relative_to(ROOT)}  {dst.stat().st_size // 1024} KB")


def main() -> None:
    for p in sorted(ROOT.glob("Figure*.png")):
        m = re.match(r"Figure(\d+[a-z]?)\.png$", p.name)
        if not m:
            print(f"SKIP (name): {p.name}")
            continue
        emit(p, ROOT / f"fig{m.group(1).lower()}.webp", SINGLE_MAX)
    for p in sorted((ROOT / "figure01").glob("*.png")):
        m = re.match(r"(\d+)_", p.name)
        if not m:
            print(f"SKIP (name): figure01/{p.name}")
            continue
        emit(p, ROOT / "fig01" / f"{int(m.group(1)):02d}.webp", GRID_MAX)


if __name__ == "__main__":
    main()
