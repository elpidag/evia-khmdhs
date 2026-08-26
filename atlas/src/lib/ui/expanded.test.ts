import { describe, expect, it } from 'vitest';
import { isExpanded, lessHref, moreHref } from './expanded';

const P = ['view', 'sel', 'money'] as const;
const u = (s: string) => new URL(s, 'http://x');

describe('the card’s unfolded state', () => {
	it('is read from the URL: a frame anchor or a chart lens opens the page unfolded', () => {
		expect(isExpanded(u('/antinero'), P)).toBe(false);
		expect(isExpanded(u('/antinero#flows'), P)).toBe(true);
		expect(isExpanded(u('/antinero#more'), P)).toBe(true);
		expect(isExpanded(u('/antinero?view=money'), P)).toBe(true);
		expect(isExpanded(u('/antinero?embed=1'), P)).toBe(false);
	});
	it('the buttons keep the query and toggle the hash', () => {
		expect(moreHref(u('/antinero?view=money'))).toBe('/antinero?view=money#more');
		expect(lessHref(u('/antinero?view=money#more'))).toBe('/antinero?view=money');
	});
});
