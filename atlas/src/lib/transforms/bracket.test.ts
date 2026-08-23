import { describe, expect, it } from 'vitest';
import { bracket } from './format';

describe('bracket', () => {
	it('makes the API bracket labels readable', () => {
		expect(bracket('0–10k')).toBe('0–10k');
		expect(bracket('500–1000k')).toBe('500k–1M');
		expect(bracket('2000–5000k')).toBe('2–5M');
		expect(bracket('>10M')).toBe('>10M');
		expect(bracket('1000–2000k')).toBe('1–2M');
	});
});
