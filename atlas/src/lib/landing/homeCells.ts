/**
 * The landing menu is a 4×4 grid (Artboard 2, user 2026-08-27). Cells are
 * data so they can be reassigned as the site grows: one cell carries the
 * drifting field, three are links, one holds the language mark the
 * artboard places top-right, the rest stay empty with their border.
 */
export type HomeCell = { r: 1 | 2 | 3 | 4; c: 1 | 2 | 3 | 4 } & (
	| { kind: 'field' }
	| { kind: 'link'; label: string; href: string; tone?: 'ink' | 'paper' }
	| { kind: 'note'; label: string }
	| { kind: 'empty' }
);

export const HOME_CELLS: HomeCell[] = [
	{ r: 1, c: 1, kind: 'field' },
	// the artboard's «GR / EN» mark — a placeholder until a Greek version exists
	{ r: 1, c: 4, kind: 'note', label: 'GR / EN' },
	{ r: 2, c: 2, kind: 'link', label: 'START HERE', href: '/story', tone: 'ink' },
	{ r: 3, c: 2, kind: 'link', label: 'EXPLORE THE DATA', href: '/data' },
	{ r: 4, c: 3, kind: 'link', label: 'METHODOLOGY', href: '/story#methodology' }
];

/** the full 4×4, row-major, empties filled in; refuses a double booking */
export function cellGrid(cells: HomeCell[] = HOME_CELLS): HomeCell[][] {
	const grid: HomeCell[][] = [1, 2, 3, 4].map((r) =>
		[1, 2, 3, 4].map((c) => ({ r, c, kind: 'empty' }) as HomeCell)
	);
	let fields = 0;
	for (const cell of cells) {
		const slot = grid[cell.r - 1][cell.c - 1];
		if (slot.kind !== 'empty') throw new Error(`cell ${cell.r},${cell.c} assigned twice`);
		if (cell.kind === 'field' && ++fields > 1) throw new Error('one field cell only');
		grid[cell.r - 1][cell.c - 1] = cell;
	}
	return grid;
}
