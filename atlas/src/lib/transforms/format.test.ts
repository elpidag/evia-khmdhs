import { describe, expect, it } from 'vitest';
import { eur, eurShort, grInt, grNumber, pct } from './format';

// Goldens mirror webui/filters.py docstrings + real KPI values — the two
// sites must print money identically.
describe('grNumber', () => {
	it('formats Greek-style', () => {
		expect(grNumber(1234567.5)).toBe('1.234.567,50');
		expect(grNumber(0)).toBe('0,00');
		expect(grNumber(1234567.5, 0)).toBe('1.234.568');
	});
	it('empty on null/undefined', () => {
		expect(grNumber(null)).toBe('');
		expect(grNumber(undefined)).toBe('');
	});
});

describe('eur', () => {
	it('appends the € sign', () => {
		expect(eur(1234567.5)).toBe('1.234.567,50 €');
		expect(eur(615950156.78)).toBe('615.950.156,78 €');
	});
});

describe('eurShort', () => {
	it('matches webui eur_short goldens', () => {
		expect(eurShort(1234567.5)).toBe('1,23 M €');
		expect(eurShort(528774383)).toBe('528,77 M €');
		expect(eurShort(615950156.78)).toBe('615,95 M €');
		expect(eurShort(41418963.96)).toBe('41,42 M €');
		expect(eurShort(1_540_000_000)).toBe('1,54 B €');
		expect(eurShort(7130.65)).toBe('7,1 K €');
		expect(eurShort(950)).toBe('950,00 €');
	});
});

describe('grInt / pct', () => {
	it('formats', () => {
		expect(grInt(2018)).toBe('2.018');
		expect(pct(90.9)).toBe('90,9%');
	});
});
