import { describe, expect, it } from 'vitest';
import { peEn, regionOfPe, pesOfRegion } from './regions';

describe('the Π.Ε. → περιφέρεια bridge (DATA_DECISIONS 2026-08-25)', () => {
	it('resolves through the curated nuts_id, familiar-English names', () => {
		expect(regionOfPe('Π.Ε. Ευβοίας')).toBe('Central Greece');
		expect(regionOfPe('Π.Ε. Ανατολικής Αττικής')).toBe('Attica');
		expect(regionOfPe('Π.Ε. Ρόδου')).toBe('South Aegean');
		expect(regionOfPe('Π.Ε. Έβρου')).toBe('Eastern Macedonia & Thrace');
		expect(regionOfPe('Π.Ε. Αχαΐας')).toBe('Western Greece');
		expect(regionOfPe(null)).toBeNull();
		expect(regionOfPe('nonsense')).toBeNull();
	});

	it('partitions all 74 Π.Ε. into the 13 regions, no leftovers', () => {
		const regions = [
			'Attica', 'North Aegean', 'South Aegean', 'Crete',
			'Eastern Macedonia & Thrace', 'Central Macedonia', 'Western Macedonia',
			'Epirus', 'Thessaly', 'Ionian Islands', 'Western Greece',
			'Central Greece', 'Peloponnese'
		];
		const all = regions.flatMap((r) => pesOfRegion(r));
		expect(all.length).toBe(74);
		expect(new Set(all).size).toBe(74);
		// every member resolves back to its own region
		for (const r of regions) for (const pe of pesOfRegion(r)) expect(regionOfPe(pe)).toBe(r);
		// a region's extent list carries real Π.Ε. (spot check)
		expect(pesOfRegion('Central Greece')).toContain('Π.Ε. Ευβοίας');
		expect(peEn('Π.Ε. Ευβοίας')).toBe('Evia');
	});
});
