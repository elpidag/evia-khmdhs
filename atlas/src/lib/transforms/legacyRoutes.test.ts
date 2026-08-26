import { describe, expect, it } from 'vitest';
import { legacyAntineroTarget } from './legacyRoutes';

describe('old Anti-nero permalinks on /', () => {
	it('forwards every query form with its parameters intact', () => {
		expect(
			legacyAntineroTarget(
				'?view=money&focus=works%3A%CE%A0.%CE%95.+%CE%95%CF%85%CE%B2%CE%BF%CE%AF%CE%B1%CF%82'
			)
		).toBe(
			'/antinero?view=money&focus=works%3A%CE%A0.%CE%95.+%CE%95%CF%85%CE%B2%CE%BF%CE%AF%CE%B1%CF%82'
		);
		expect(legacyAntineroTarget('?sel=24SYMV014492614')).toBe('/antinero?sel=24SYMV014492614');
		expect(legacyAntineroTarget('?money=paid')).toBe('/antinero?money=paid');
		expect(legacyAntineroTarget('?net=type&rank=firm')).toBe('/antinero?net=type&rank=firm');
	});
	it('forwards a hash to a frame of the old page, and keeps a query with it', () => {
		expect(legacyAntineroTarget('', '#flows')).toBe('/antinero#flows');
		expect(legacyAntineroTarget('?flows=company', '#flows')).toBe('/antinero?flows=company#flows');
	});
	it('leaves the landing alone otherwise', () => {
		expect(legacyAntineroTarget('')).toBeNull();
		expect(legacyAntineroTarget('?menu=1')).toBeNull();
		expect(legacyAntineroTarget('?embed=1')).toBeNull();
		expect(legacyAntineroTarget('', '#somewhere-else')).toBeNull();
	});
});
