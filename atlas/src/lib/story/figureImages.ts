/**
 * The story figures the author has delivered as IMAGES (DATA_DECISIONS
 * 2026-09-02) — keyed like `figures.ts` by the author's own figure number.
 * The files are the small .webp derivatives `scripts/build_story_images.py`
 * emits from the full-size originals (which stay gitignored on disk);
 * `figureImages.test.ts` pins every entry to an existing marker AND an
 * existing file, so a renumbering or a missing build fails loudly.
 *
 *  · `grid`  — Figure 01: the author's 18 square press/satellite images as
 *    SIX ROWS OF THREE, in their filename order (1,2,3 the first row left
 *    to right, 4,5,6 the second, …) — the author's ruling of 2026-09-02.
 *  · `pair`  — two square images side by side (Figure 02's a + b).
 *  · `single` — one square image in the slot.
 */
export interface FigureImage {
	/** `pair` is a carousel (one at a time, an arrow); `slider` shows both at
	 *  once — the second underneath, the first revealed left of a handle the
	 *  reader drags across (figure 23's two land-use maps, the author,
	 *  2026-09-03) */
	kind: 'single' | 'pair' | 'grid' | 'slider';
	srcs: string[];
	/** LIFT the block to the column's top instead of the shared centred
	 *  placement — for a figure whose caption needs the room below */
	lift?: boolean;
	/** draw the image at this fraction of the slot's width (figures 22 and
	 *  25 at 0.85 — «a bit weird» at full size, the author, 2026-09-03) */
	scale?: number;
}

const one = (s: string): FigureImage => ({ kind: 'single', srcs: [`/img/story/${s}`] });

export const FIGURE_IMAGES: Record<number, FigureImage> = {
	1: {
		kind: 'grid',
		srcs: Array.from({ length: 18 }, (_, i) => `/img/story/fig01/${String(i + 1).padStart(2, '0')}.webp`)
	},
	2: { kind: 'pair', srcs: ['/img/story/fig02a.webp', '/img/story/fig02b.webp'] },
	3: one('fig03.webp'),
	// delivered 2026-09-03: the press conference, the two land-use maps
	// and the two sponsor images as carousels, the antinero image, the
	// protest — leaving 04 and 10 to the live drawings
	5: { ...one('fig05.webp'), scale: 0.85 },
	6: { kind: 'slider', srcs: ['/img/story/fig06a.webp', '/img/story/fig06b.webp'], lift: true },
	7: { kind: 'pair', srcs: ['/img/story/fig07a.webp', '/img/story/fig07b.webp'] },
	8: { ...one('fig08.webp'), scale: 0.85 },
	9: one('fig09.webp'),
	11: one('fig11.webp'),
	12: one('fig12.webp'),
	13: one('fig13.webp')
};
