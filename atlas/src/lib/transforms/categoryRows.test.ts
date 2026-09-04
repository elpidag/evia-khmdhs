import { describe, expect, it } from 'vitest';
import { categoryRows, lowerRows, splitHint } from './categoryRows';

const CATS = [
	{ key: 'a', label: 'Α', label_en: 'Studies: fire-protection plans', n: 14, eur: 100 },
	{ key: 'b', label: 'Β', label_en: 'Special forestry works (the catch-all)', n: 160, eur: 900 },
	{
		key: 'c',
		label: 'Γ',
		label_en: 'National Reforestation Plan',
		n: 9,
		eur: 300,
		names: [{ label_en: 'Planting', n: 4 }]
	}
];

describe('the CONTRACT TYPE rows, shared by the page and the story', () => {
	it('sorts by the lens, biggest first', () => {
		expect(categoryRows(CATS, 'eur').map((r) => r.value)).toEqual([900, 300, 100]);
		expect(categoryRows(CATS, 'n').map((r) => r.value)).toEqual([160, 14, 9]);
	});

	it('lower-cases only the opening letter, so proper nouns survive', () => {
		expect(lowerRows([{ label: 'National Reforestation Plan' }])[0].label).toBe(
			'national Reforestation Plan'
		);
	});

	it('moves the explanatory tail into the hint', () => {
		expect(splitHint('studies: fire-protection plans')).toEqual({
			label: 'studies',
			hint: 'including fire-protection plans'
		});
		expect(splitHint('special forestry works (the catch-all)')).toEqual({
			label: 'special forestry works',
			hint: 'the catch-all'
		});
		expect(splitHint('plain name')).toEqual({ label: 'plain name' });
	});

	it('names the works in the hover, counts included', () => {
		const rows = categoryRows(CATS, 'eur');
		expect(rows[1].title).toBe('National Reforestation Plan — 9 contracts. Works named: planting 4');
		expect(rows[0].hint).toBe('the catch-all');
	});
});
