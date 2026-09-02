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
	kind: 'single' | 'pair' | 'grid';
	srcs: string[];
}

const one = (s: string): FigureImage => ({ kind: 'single', srcs: [`/img/story/${s}`] });

export const FIGURE_IMAGES: Record<number, FigureImage> = {
	1: {
		kind: 'grid',
		srcs: Array.from({ length: 18 }, (_, i) => `/img/story/fig01/${String(i + 1).padStart(2, '0')}.webp`)
	},
	2: { kind: 'pair', srcs: ['/img/story/fig02a.webp', '/img/story/fig02b.webp'] },
	3: one('fig03.webp'),
	11: one('fig11.webp'),
	13: one('fig13.webp')
};
