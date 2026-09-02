
## 2026-09-03 — one placement for every figure, and figure 02 becomes a carousel

The author's follow-up: the grid drops 40 px further (60 below the
column's centre in all), the caption 7 px under the image — and that
PLACEMENT APPLIES TO EVERY FIGURE. `StoryFigure` was rebuilt around one
`.stack` (absolute, flex-centred, translateY 60 px): grid packs, singles,
the carousel, the live drawing and the placeholder square all ride it,
caption and credit below. Figure 02's two images are a CAROUSEL — one
image in the standard 540 slot, a small round arrow on its right edge
interchanging them (state resets on figure change); the 75%-stacked
arrangement of the same day is superseded. Measured: block mid = column
mid + 60 and caption gap 7,0 px on grid, carousel and single alike; the
arrow swaps 02a → 02b. The dormant footnote machinery rode along
unchanged.
