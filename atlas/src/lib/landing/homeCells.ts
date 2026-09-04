/**
 * The landing menu is a 4×4 grid — the author's artboard of 2026-09-04
 * (`landing_menu.svg`, the second drawing of it): three text links, the
 * network drawing, the author's own SCHEMATIC drawings of the data
 * (`static/img/symbols/landing*.svg`: the co-op values as a swarm across
 * two rows, a stacked column, a run of bars, Εύβοια across two columns,
 * the sponsors' plant) and fire image, and STILL fields of codes in the
 * cells left white. Cells are data so they can be reassigned as the site
 * grows; two of them SPAN a second row or column, and a drawing sits in
 * its cell at the artboard's own offsets (fractions of the cell).
 */
export type Slot = { r: 1 | 2 | 3 | 4; c: 1 | 2 | 3 | 4; rs?: 2; cs?: 2 };

export type HomeCell = Slot &
	(
		| {
				/** a still field of codes; `field` marks the ONE cell the opening
				 *  animation collapses into (the page renders its own field there) */
				kind: 'codes';
				field?: true;
		  }
		| {
				kind: 'link';
				label: string;
				href: string;
				/** 36 px (the artboard's START HERE) or 24 px */
				size?: 'lg' | 'md';
				color?: string;
				/** top-right (default) or bottom-right of the cell */
				at?: 'top' | 'bottom';
		  }
		| {
				/** one of the site's symbols (`datasets.ts`), centred */
				kind: 'symbol';
				key: string;
				href: string;
				/** width as a fraction of the cell */
				size: number;
		  }
		| {
				/** a drawing or image placed as the artboard places it: its left
				 *  edge, its top and its width as fractions of the cell (the
				 *  height follows the file's own shape) */
				kind: 'image';
				src: string;
				alt: string;
				left: number;
				top: number;
				width: number;
				href?: string;
		  }
	);

/** a slot under a spanning neighbour: rendered by nobody */
export type GridSlot = HomeCell | (Slot & { kind: 'covered' });

const SYM = '/img/symbols/';

export const HOME_CELLS: HomeCell[] = [
	{ r: 1, c: 1, kind: 'codes', field: true },
	{ r: 1, c: 2, kind: 'codes' },
	{ r: 1, c: 3, kind: 'symbol', key: 'actors', href: '/authorities', size: 0.6 },
	{ r: 1, c: 4, kind: 'codes' },
	{
		r: 2,
		c: 1,
		kind: 'link',
		label: 'START HERE',
		href: '/story',
		size: 'lg',
		color: 'var(--c-dase)',
		at: 'top'
	},
	// the co-op contract values as a swarm, the median dashed — across two rows
	{
		r: 2,
		c: 2,
		rs: 2,
		kind: 'image',
		src: SYM + 'landinggraph03.svg',
		alt: 'Contract values as a swarm of dots',
		left: 0.005,
		top: 0.034,
		width: 0.99
	},
	{ r: 2, c: 3, kind: 'link', label: 'EXPLORE THE DATA', href: '/data', at: 'bottom' },
	{
		r: 2,
		c: 4,
		kind: 'image',
		src: '/img/landing/bs-distorted.webp',
		alt: 'The burnt areas of Greece, drawn by the author',
		left: 0,
		top: 0.04,
		width: 1
	},
	{ r: 3, c: 1, kind: 'link', label: 'METHODOLOGY', href: '/story#methodology', at: 'bottom' },
	{ r: 3, c: 3, kind: 'codes' },
	// a stacked column in the three streams' tones
	{
		r: 3,
		c: 4,
		kind: 'image',
		src: SYM + 'landinggraph02.svg',
		alt: 'A stacked column',
		left: 0.137,
		top: 0.04,
		width: 0.49
	},
	// a run of bars, the ranking's shape
	{
		r: 4,
		c: 1,
		kind: 'image',
		src: SYM + 'landinggraph01.svg',
		alt: 'A ranking of bars',
		left: 0.05,
		top: 0.05,
		width: 0.84
	},
	// the sponsors' plant, its stem reaching the cell's bottom rule
	{
		r: 4,
		c: 2,
		kind: 'image',
		src: SYM + 'landingtree.svg',
		alt: 'A tree — the works financed by private companies',
		left: 0.195,
		top: 0.083,
		width: 0.69,
		href: '/anadohoi'
	},
	// Εύβοια — across two columns
	{
		r: 4,
		c: 3,
		cs: 2,
		kind: 'image',
		src: SYM + 'landingmap.svg',
		alt: 'The island of Evia',
		left: 0.21,
		top: 0.075,
		width: 0.77
	}
];

/** the full 4×4, row-major: every cell at its origin, the slots under a
 *  span marked `covered`; refuses a double booking, a span past the edge
 *  and a second flight-target field */
export function cellGrid(cells: HomeCell[] = HOME_CELLS): GridSlot[][] {
	const grid: (GridSlot | null)[][] = [1, 2, 3, 4].map(() => [null, null, null, null]);
	let fields = 0;
	for (const cell of cells) {
		const rs = cell.rs ?? 1;
		const cs = cell.cs ?? 1;
		if (cell.r + rs - 1 > 4 || cell.c + cs - 1 > 4) {
			throw new Error(`cell ${cell.r},${cell.c} spans past the grid`);
		}
		if (cell.kind === 'codes' && cell.field && ++fields > 1) {
			throw new Error('one field cell only');
		}
		for (let r = cell.r; r < cell.r + rs; r++) {
			for (let c = cell.c; c < cell.c + cs; c++) {
				if (grid[r - 1][c - 1]) throw new Error(`cell ${r},${c} assigned twice`);
				grid[r - 1][c - 1] =
					r === cell.r && c === cell.c
						? cell
						: ({ r, c, kind: 'covered' } as GridSlot);
			}
		}
	}
	return grid.map((row, r) =>
		row.map((slot, c) => slot ?? ({ r: r + 1, c: c + 1, kind: 'codes' } as GridSlot))
	);
}

/** the CSS grid-area of a cell: its origin and its spans */
export function gridArea(cell: Slot): string {
	return `${cell.r} / ${cell.c} / span ${cell.rs ?? 1} / span ${cell.cs ?? 1}`;
}
