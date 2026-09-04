import { describe, expect, it } from 'vitest';
import { HOME_CELLS, cellGrid, gridArea, type HomeCell } from './homeCells';

describe('the landing grid (the author’s artboard of 2026-09-04)', () => {
	it('is a full 4×4: the three links, the network, the author’s drawings and image, still codes', () => {
		const g = cellGrid();
		expect(g.length).toBe(4);
		expect(g.every((row) => row.length === 4)).toBe(true);
		// the flight target, top-left, and the other white cells as still codes
		expect(g[0][0]).toMatchObject({ kind: 'codes', field: true });
		expect(g[0][1].kind).toBe('codes');
		expect(g[0][3].kind).toBe('codes');
		expect(g[2][2].kind).toBe('codes');
		expect(g.flat().filter((c) => c.kind === 'codes').length).toBe(4);
		// the links: START HERE big and green top-right, the two others bottom-right
		expect(g[1][0]).toMatchObject({ kind: 'link', href: '/story', size: 'lg', at: 'top' });
		expect(g[1][2]).toMatchObject({ kind: 'link', href: '/data', at: 'bottom' });
		expect(g[2][0]).toMatchObject({ kind: 'link', href: '/story#methodology', at: 'bottom' });
		// the author's drawings, two of them spanning
		expect(g[1][1]).toMatchObject({ kind: 'image', rs: 2, src: '/img/symbols/landinggraph03.svg' });
		expect(g[2][1]).toMatchObject({ kind: 'covered' });
		expect(g[3][2]).toMatchObject({ kind: 'image', cs: 2, src: '/img/symbols/landingmap.svg' });
		expect(g[3][3]).toMatchObject({ kind: 'covered' });
		expect(g[2][3]).toMatchObject({ kind: 'image', src: '/img/symbols/landinggraph02.svg' });
		expect(g[3][0]).toMatchObject({ kind: 'image', src: '/img/symbols/landinggraph01.svg' });
		expect(g[3][1]).toMatchObject({ kind: 'image', src: '/img/symbols/landingtree.svg', href: '/anadohoi' });
		expect(g[1][3]).toMatchObject({ kind: 'image', src: '/img/landing/bs-distorted.webp' });
		expect(g[0][2]).toMatchObject({ kind: 'symbol', key: 'actors', href: '/authorities' });
		// every drawing sits inside its cell: offsets and widths are fractions
		for (const c of g.flat()) {
			if (c.kind === 'image') {
				expect(c.left).toBeGreaterThanOrEqual(0);
				expect(c.top).toBeGreaterThanOrEqual(0);
				expect(c.left + c.width).toBeLessThanOrEqual(1);
			}
		}
	});
	it('places a spanning cell by its origin and spans', () => {
		expect(gridArea({ r: 2, c: 2, rs: 2 })).toBe('2 / 2 / span 2 / span 1');
		expect(gridArea({ r: 4, c: 3, cs: 2 })).toBe('4 / 3 / span 1 / span 2');
		expect(gridArea({ r: 1, c: 1 })).toBe('1 / 1 / span 1 / span 1');
	});
	it('refuses a double booking, a slot under a span, a span past the edge and a second field', () => {
		expect(() => cellGrid([...HOME_CELLS, { r: 1, c: 1, kind: 'codes' }])).toThrow();
		expect(() => cellGrid([...HOME_CELLS, { r: 3, c: 2, kind: 'codes' }])).toThrow();
		expect(() =>
			cellGrid([
				{ r: 4, c: 4, cs: 2, kind: 'image', src: 'x', alt: 'x', left: 0, top: 0, width: 1 } as HomeCell
			])
		).toThrow();
		expect(() => cellGrid([...HOME_CELLS, { r: 4, c: 4, kind: 'codes', field: true }])).toThrow();
	});
});
