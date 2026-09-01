/**
 * The words the story's Figure 04 prints: the clock in Athens time and the
 * card's line for an alert. Athens is a FIXED +03:00 through the window
 * (every timestamp in the file carries it), so no ICU time zone is needed
 * and the string is the same on every machine — alertsText.test.ts pins
 * each alert's clock string against its own ISO fields.
 */
import type { Alert, Place } from './alerts';

const ATHENS = 3 * 3_600_000;
const MON = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'];

/** the Athens wall-clock fields of an instant */
export function athens(ms: number): { y: number; m: number; d: number; hh: number; mm: number } {
	const t = new Date(ms + ATHENS);
	return {
		y: t.getUTCFullYear(),
		m: t.getUTCMonth(),
		d: t.getUTCDate(),
		hh: t.getUTCHours(),
		mm: t.getUTCMinutes()
	};
}

const two = (n: number) => String(n).padStart(2, '0');

/** «5 Aug 2021 · 16:48» */
export function formatClock(ms: number): string {
	const a = athens(ms);
	return `${a.d} ${MON[a.m]} ${a.y} · ${two(a.hh)}:${two(a.mm)}`;
}

/** «5 Aug» — the day strip's labels */
export function formatDay(ms: number): string {
	const a = athens(ms);
	return `${a.d} ${MON[a.m]}`;
}

export const namesOf = (ps: Place[]): string => ps.map((p) => p.nameEn).join(', ');

/** the card's second line: who was sent where, in the message's own order */
export function cardLine(a: Alert): string {
	const orders = a.orders.filter((o) => o.from.length || o.to.length);
	if (!orders.length) return a.title ?? '';
	if (a.type === 'shelter_in_place') {
		return `${namesOf(orders.flatMap((o) => o.from))} · stay indoors`;
	}
	if (a.type === 'fire_danger' || a.type === 'general') {
		return a.title || namesOf(orders.flatMap((o) => [...o.from, ...o.to]));
	}
	return orders
		.map((o) => (o.to.length ? `${namesOf(o.from)} → ${namesOf(o.to)}` : namesOf(o.from)))
		.join(' · ');
}
