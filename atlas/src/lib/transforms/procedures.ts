/**
 * The awarding procedure in English, using Directive 2014/24/EU's own
 * wording for the procedures it defines (user, 2026-08-19 — the contract
 * card is an English page and cannot mix the two languages).
 *
 * ν.4412/2016 transposes the Directive, so the registry's Greek strings map
 * onto it one for one:
 *
 *   Ανοικτή διαδικασία (αρ. 27)          → Open procedure          (art. 27)
 *   Διαπραγμάτευση χωρίς προηγούμενη
 *     δημοσίευση (αρ. 32)                → Negotiated procedure without
 *                                          prior publication       (art. 32)
 *   Κατεπείγουσα ανάγκη οφειλόμενη σε
 *     γεγονότα απρόβλεπτα…               → the Directive's art. 32(2)(c)
 *                                          ground, quoted in its English
 *
 * «Απευθείας ανάθεση» has no Directive equivalent: άρθρο 118 (and 328 for
 * utilities) is Greece's own below-threshold route, so it keeps the plain
 * English «Direct award» with its article reference. Article numbers stay
 * literal — they are identifiers, not prose.
 */
const RULES: [RegExp, string][] = [
	[/ΑΝΟΙ[ΧΚ]Τ/, 'Open procedure'],
	[/ΚΛΕΙΣΤ/, 'Restricted procedure'],
	[/ΑΝΤΑΓΩΝΙΣΤΙΚ[ΟΗ]Σ?\s*ΔΙΑΛΟΓΟΣ|ΑΝΤΑΓΩΝΙΣΤΙΚΟΥ ΔΙΑΛΟΓΟΥ/, 'Competitive dialogue'],
	[/ΣΥΜΠΡΑΞΗ ΚΑΙΝΟΤΟΜΙΑΣ/, 'Innovation partnership'],
	[/ΔΙΑΠΡΑΓΜΑΤΕΥΣΗ.*ΧΩΡΙΣ/, 'Negotiated procedure without prior publication'],
	[/ΔΙΑΠΡΑΓΜΑΤΕΥΣΗ/, 'Negotiated procedure'],
	[/ΑΠΕΥΘΕΙΑΣ ΑΝΑΘΕΣΗ/, 'Direct award'],
	[/ΣΥΝΟΠΤΙΚΟΣ ΔΙΑΓΩΝΙΣΜΟΣ/, 'Simplified competition'],
	[/ΚΑΤΕΠΕΙΓΟΥΣΑ ΑΝΑΓΚΗ/, 'Extreme urgency brought about by events unforeseeable by the contracting authority']
];

const fold = (s: string): string =>
	s
		.toUpperCase()
		.normalize('NFD')
		.replace(/[̀-ͯ]/g, '');

/** «(αρ.118/αρ. 328)» — kept verbatim, they identify the article */
const ARTICLES = /\(([^)]*(?:αρ|άρθρ)[^)]*)\)/i;

/**
 * English name for a registry procedure string, with its article reference
 * preserved. Returns the original when nothing matches — an unknown Greek
 * string is better than a wrong English one.
 */
export function procedureEn(raw: string | null | undefined): string {
	if (!raw) return '—';
	const f = fold(raw);
	const hit = RULES.find(([rx]) => rx.test(f));
	if (!hit) return raw;
	const art = raw.match(ARTICLES);
	const refs = art
		? art[1]
				.replace(/άρθρ(ο|ου)?/gi, 'art.')
				.replace(/αρ\./gi, 'art.')
				.replace(/\s+/g, ' ')
				.trim()
		: '';
	return refs ? `${hit[1]} (${refs})` : hit[1];
}
