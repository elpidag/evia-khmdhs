import { describe, expect, it } from 'vitest';
import { ALERTS, type Alert } from './alerts';
import { cardLine, formatClock, formatDay, namesOf } from './alertsText';

describe('the clock strings', () => {
	it("print every alert's own Athens fields", () => {
		for (const a of ALERTS) {
			const m = /^(\d{4})-(\d{2})-(\d{2})T(\d{2}):(\d{2}):\d{2}\+03:00$/.exec(a.timestamp);
			expect(m, a.timestamp).not.toBeNull();
			const [, y, mo, d, hh, mm] = m!;
			const mon = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'][
				Number(mo) - 1
			];
			expect(formatClock(Date.parse(a.timestamp))).toBe(`${Number(d)} ${mon} ${y} · ${hh}:${mm}`);
			expect(formatDay(Date.parse(a.timestamp))).toBe(`${Number(d)} ${mon}`);
		}
	});

	it('crosses midnight in Athens, not in UTC', () => {
		expect(formatClock(Date.parse('2021-08-05T00:30:00+03:00'))).toBe('5 Aug 2021 · 00:30');
		expect(formatClock(Date.parse('2021-08-04T23:30:00+03:00'))).toBe('4 Aug 2021 · 23:30');
	});
});

describe('the card line', () => {
	const base = { tweetId: 'x', timestamp: '2021-08-05T10:00:00+03:00', region: 'evia', text: '', url: '' };
	const p = (nameEn: string) => ({ tag: nameEn, nameEn, lat: 38, lon: 23, source: 'hand' });

	it('writes an evacuation as from → to, one order at a time', () => {
		const a: Alert = {
			...base,
			type: 'evacuation',
			orders: [
				{ from: [p('Agia Anna'), p('Kerameia')], to: [p('Mantoudi')] },
				{ from: [p('Kechries')], to: [p('Limni'), p('Rovies')] }
			]
		};
		expect(cardLine(a)).toBe('Agia Anna, Kerameia → Mantoudi · Kechries → Limni, Rovies');
	});

	it('names the destination-less order alone', () => {
		const a: Alert = { ...base, type: 'evacuation', orders: [{ from: [p('Limni')], to: [] }] };
		expect(cardLine(a)).toBe('Limni');
	});

	it('says stay indoors for a shelter order', () => {
		const a: Alert = {
			...base,
			type: 'shelter_in_place',
			orders: [{ from: [p('Istiaia'), p('Aidipsos')], to: [] }]
		};
		expect(cardLine(a)).toBe('Istiaia, Aidipsos · stay indoors');
	});

	it('prints the curated gloss for a place-less warning', () => {
		const a: Alert = { ...base, type: 'fire_danger', orders: [{ from: [], to: [] }], title: 'Extreme fire danger tomorrow' };
		expect(cardLine(a)).toBe('Extreme fire danger tomorrow');
	});

	it('every real alert has a non-empty card line', () => {
		for (const a of ALERTS) expect(cardLine(a), a.tweetId).not.toBe('');
		expect(namesOf([p('A'), p('B')])).toBe('A, B');
	});
});
