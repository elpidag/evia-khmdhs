import { describe, expect, it } from 'vitest';
import { HOME_CELLS, cellGrid } from './homeCells';

describe('the landing grid', () => {
	it('is a full 4×4 with the three links and one field cell where the mock puts them', () => {
		const g = cellGrid();
		expect(g.length).toBe(4);
		expect(g.every((row) => row.length === 4)).toBe(true);
		expect(g[0][0].kind).toBe('field');
		expect(g[1][1]).toMatchObject({
			kind: 'link',
			href: '/story',
			tone: 'ink'
		});
		expect(g[2][1]).toMatchObject({ kind: 'link', href: '/data' });
		expect(g[3][2]).toMatchObject({ kind: 'link', href: '/methodology' });
		// Artboard 2's «GR / EN» mark in the top-right cell
		expect(g[0][3]).toMatchObject({ kind: 'note', label: 'GR / EN' });
		expect(g.flat().filter((c) => c.kind === 'empty').length).toBe(11);
	});
	it('refuses a double booking and a second field', () => {
		expect(() => cellGrid([...HOME_CELLS, { r: 1, c: 1, kind: 'empty' }])).toThrow();
		expect(() => cellGrid([...HOME_CELLS, { r: 4, c: 4, kind: 'field' }])).toThrow();
	});
});
