/** Shared builder for the sponsor-project hover card — the TIMELINE's
 *  row card, reused by the map dots and the METRICS waffle so all three
 *  speak the same hover language. */
import { dmy, eurShort } from '$lib/transforms/format';
import { COLOR, NODATE_COLOR, noDate, type GanttProject } from './ganttTheme';

/** English renderings of the duration-based deadlines (shown on hover;
 *  the act's own Greek wording stays printed on the project page) */
export const DTEXT_EN: Record<string, string> = {
	'15 ημέρες από την έκδοση': '15 days from issue of the act',
	'2 έτη από την υπογραφή': '2 years from signing',
	'3 έτη από την υπογραφή': '3 years from signing',
	'4 μήνες από την έκδοση': '4 months from issue of the act',
	'4 μήνες από την έναρξη εργασιών (μέγ. 6)': '4 months from start of works (max 6)',
	'5 έτη από την έκδοση': '5 years from issue of the act',
	'5 μήνες από την έναρξη εργασιών': '5 months from start of works',
	'μελέτες: 30 ημέρες από επιλογή μελετητή · έργο: 4 μήνες από έναρξη (μέγ. 6)':
		'studies: 30 days from selecting the engineer · works: 4 months from start (max 6)',
	'μελέτη: 2 μήνες · έργο: 12 μήνες από την έναρξη':
		'study: 2 months · works: 12 months from start'
};

/** display form of a company name: uppercase per the Greek all-caps
 *  convention — the τόνος is dropped but the dialytika is KEPT (ϊ → Ϊ,
 *  so TATOΪ stays TATOΪ, not TATOI) */
export function displayName(name: string): string {
	return name
		.toUpperCase()
		.normalize('NFD')
		.replace(/[̀-̇̉-ͯ]/g, '')
		.normalize('NFC');
}

export interface CardData {
	name: string;
	color: string;
	/** text colour — dark ink on the pale no-date background */
	ink: string;
	lines: string[];
}

export function cardFor(p: GanttProject): CardData {
	const b1 = p.budget_stated ?? null;
	const b0 = p.start0 ? (p.budget0 ?? null) : null;
	const lines: string[] = [];
	lines.push(
		`designation act: ${dmy(p.start0 ?? p.start) || '—'}${p.start0 ? ` (restated ${dmy(p.start) || '—'})` : ''}`
	);
	lines.push(
		b0 !== null && b1 !== null
			? `budget announced: ${eurShort(b0)} → ${eurShort(b1)}`
			: b1 !== null
				? `budget announced: ${eurShort(b1)}`
				: 'budget announced: none stated'
	);
	if (p.deadline) {
		lines.push(
			p.deadline0 && p.deadline0 !== p.deadline
				? `deadline: ${dmy(p.deadline0)} → ${dmy(p.deadline)}`
				: `deadline: ${dmy(p.deadline)}`
		);
	} else if (p.dtext) {
		lines.push(`deadline: ${DTEXT_EN[p.dtext] ?? p.dtext}`);
	} else {
		lines.push('deadline: —');
	}
	return {
		name: displayName(p.company),
		color: noDate(p) ? NODATE_COLOR : (COLOR[p.status] ?? 'var(--ink)'),
		ink: noDate(p) ? 'var(--ink)' : 'var(--paper)',
		lines
	};
}
