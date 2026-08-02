import { describe, expect, it } from 'vitest';
import golden from './search.golden.json';
import { matches, phoneticFold, searchNorm } from './search';

describe('search normalisation matches the Python originals', () => {
	for (const g of golden as { in: string; norm: string; fold: string }[]) {
		it(`norm+fold ${JSON.stringify(g.in)}`, () => {
			expect(searchNorm(g.in)).toBe(g.norm);
			expect(phoneticFold(searchNorm(g.in))).toBe(g.fold);
		});
	}
});

describe('matches', () => {
	function q(needle: string, ...hay: string[]) {
		const n = searchNorm(needle);
		return matches(n, phoneticFold(n), ...hay);
	}
	it('Greeklish finds Greek', () => {
		expect(q('evias', 'Π.Ε. Ευβοίας')).toBe(true);
		expect(q('thessalonikis', 'Θεσσαλονίκης')).toBe(true);
		expect(q('kanellopoulou', 'Ίδρυμα Κανελλοπούλου')).toBe(true);
		// Known phonetic-space limitation shared with the Python original:
		// Greek ρ folds to visual P, so an 'r' query misses it.
		expect(q('parni8as', 'Δασαρχείο Πάρνηθας')).toBe(false);
	});
	it('accent-insensitive Greek finds Greek', () => {
		expect(q('ευβοιας', 'Π.Ε. Ευβοίας')).toBe(true);
	});
	it('homoglyph soup finds antinero', () => {
		expect(q('antinero', 'ΑΝΤΙΝΕΡΟ ΙΙΙ')).toBe(true);
	});
	it('non-matches stay out', () => {
		expect(q('kavala', 'Π.Ε. Ευβοίας')).toBe(false);
	});
});
