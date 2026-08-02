/**
 * Client-side port of the Greeklish-tolerant search from webui/queries.py
 * (_search_norm / _phonetic_fold / _matches) so /explore can filter 2.3k
 * rows instantly without server round-trips. Behaviour is pinned by golden
 * fixtures generated from the Python functions (search.golden.json).
 */

// Greek capitals visually identical to Latin capitals (khmdhs/scope.py).
const HOMOGLYPHS: Record<string, string> = {
	Α: 'A', Β: 'B', Ε: 'E', Ζ: 'Z', Η: 'H', Ι: 'I', Κ: 'K',
	Μ: 'M', Ν: 'N', Ο: 'O', Ρ: 'P', Τ: 'T', Υ: 'Y', Χ: 'X'
};

function normalizeTitle(s: string): string {
	const upper = s.toUpperCase().replaceAll('ΑΝΤΙΝΕΡΟ', 'ANTINERO');
	let out = '';
	for (const ch of upper) out += HOMOGLYPHS[ch] ?? ch;
	return out;
}

/** Accent-, case- and homoglyph-insensitive form for substring search. */
export function searchNorm(s: string | null | undefined): string {
	const stripped = (s ?? '').normalize('NFD').replace(/\p{M}/gu, '');
	return normalizeTitle(stripped);
}

// Ordered rewrite rules — digraphs first (webui/queries.py _PHONETIC_RULES).
const PHONETIC_RULES: [string, string][] = [
	['CH', 'X'], ['TH', '8'], ['Θ', '8'],
	['EY', 'EV'], ['AY', 'AV'], ['OY', 'U'], ['OU', 'U'],
	['OI', 'I'], ['EI', 'I'], ['AI', 'E'],
	['Γ', 'G'], ['Δ', 'D'], ['Λ', 'L'], ['Ξ', 'X'], ['Π', 'P'],
	['Σ', 'S'], ['Φ', 'F'], ['Ψ', 'PS'], ['Ω', 'O'],
	['Y', 'I'], ['H', 'I'], ['B', 'V']
];

/** Fold a searchNorm() output into the shared phonetic space and collapse
 *  doubled letters ("EVVIAS" → "EVIAS"; digits are kept doubled). */
export function phoneticFold(normed: string): string {
	let s = normed;
	for (const [a, b] of PHONETIC_RULES) s = s.replaceAll(a, b);
	let out = '';
	for (const ch of s) {
		if (!out || out[out.length - 1] !== ch || /[0-9]/.test(ch)) out += ch;
	}
	return out;
}

/** True when the query matches any haystack (substring in either space). */
export function matches(
	needleNorm: string,
	needleFold: string,
	...haystacks: (string | null | undefined)[]
): boolean {
	for (const h of haystacks) {
		const hn = searchNorm(h);
		if (hn.includes(needleNorm) || phoneticFold(hn).includes(needleFold)) {
			return true;
		}
	}
	return false;
}
