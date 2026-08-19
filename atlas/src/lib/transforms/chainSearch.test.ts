import { describe, expect, it } from 'vitest';
import { matches, phoneticFold, searchNorm } from './search';

/**
 * /explore ships ONE row per Anti-nero contract-chain, so the row must answer
 * to every ΑΔΑΜ of that chain — citing the σύμβαση itself must not return
 * «nothing matches» because a later act on it is the record in scope
 * (DATA_DECISIONS 2026-08-19).
 *
 * This pins the index string the page builds, not the page itself: the row's
 * own ref plus `alt`, then title, contractor and regions.
 */
interface Row {
	ref: string;
	alt?: string[];
	t: string;
	co: string;
	pe: string[];
	hq: string[];
}
const row: Row = {
	ref: '26SYMV018978343',
	alt: ['25SYMV017345053'],
	t: 'ΣΥΜΒΑΣΗ ΕΚΤΕΛΕΣΗΣ ΕΡΓΟΥ ANTINERO IV ΑΤΤΙΚΗΣ ΚΑΙ ΟΜΟΡΩΝ ΠΕ',
	co: 'ΚΑΡΑΛΗ ΔΕΣΠΟΙΝΑ ΤΟΥ ΒΑΣΙΛΕΙΟΥ',
	pe: ['Π.Ε. Ανατολικής Αττικής'],
	hq: []
};
const index = (r: Row) =>
	searchNorm(`${r.ref} ${(r.alt ?? []).join(' ')} ${r.t} ${r.co} ${r.pe.join(' ')} ${r.hq.join(' ')}`);

function hits(q: string, r: Row = row): boolean {
	const n = searchNorm(q);
	return matches(n, phoneticFold(n), index(r));
}

describe('chain rows answer to every ΑΔΑΜ of the chain', () => {
	it('finds the row by the record that is in scope', () => {
		expect(hits('26SYMV018978343')).toBe(true);
	});

	it('finds the row by an EARLIER version — the contract itself', () => {
		expect(hits('25SYMV017345053')).toBe(true);
	});

	it('still finds it by title and by contractor', () => {
		expect(hits('ANTINERO IV ΑΤΤΙΚΗΣ')).toBe(true);
		expect(hits('ΚΑΡΑΛΗ')).toBe(true);
	});

	it('does not match an unrelated ΑΔΑΜ', () => {
		expect(hits('26SYMV019098206')).toBe(false);
	});

	it('a contract posted once carries no alt and still matches itself', () => {
		const solo = { ...row, ref: '22SYMV010785854', alt: undefined };
		expect(hits('22SYMV010785854', solo)).toBe(true);
	});
});
