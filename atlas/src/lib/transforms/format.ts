/**
 * Greek-style number/€ formatting — a TS port of webui/filters.py.
 * The golden tests in format.test.ts pin the output to the Python filters'
 * documented behaviour so both sites always print money identically.
 */

export function grNumber(n: number | null | undefined, decimals = 2): string {
	if (n === null || n === undefined || Number.isNaN(n)) return '';
	const s = n.toLocaleString('en-US', {
		minimumFractionDigits: decimals,
		maximumFractionDigits: decimals
	});
	// 1,234,567.50 -> 1.234.567,50
	return s.replace(/,/g, 'X').replace(/\./g, ',').replace(/X/g, '.');
}

export function eur(n: number | null | undefined): string {
	if (n === null || n === undefined || Number.isNaN(n)) return '';
	return `${grNumber(n)} €`;
}

export function eurShort(n: number | null | undefined): string {
	if (n === null || n === undefined || Number.isNaN(n)) return '';
	const v = Math.abs(n);
	if (v >= 1_000_000_000) return `${grNumber(n / 1_000_000_000, 2)} B €`;
	if (v >= 1_000_000) return `${grNumber(n / 1_000_000, 2)} M €`;
	if (v >= 1_000) return `${grNumber(n / 1_000, 1)} K €`;
	return eur(n);
}

/**
 * The shortest honest form of an amount — for printing INSIDE a mark, where
 * «11,63 M €» does not fit but «11,6M» does. Presentation only: no chart
 * states a total in this form, and `eurShort` stays the site's money format.
 */
export function eurTiny(n: number | null | undefined): string {
	if (n === null || n === undefined || Number.isNaN(n)) return '';
	const v = Math.abs(n);
	if (v >= 1_000_000_000) return `${grNumber(n / 1_000_000_000, 1)}B`;
	if (v >= 1_000_000) return `${grNumber(n / 1_000_000, 1)}M`;
	if (v >= 1_000) return `${grNumber(Math.round(n / 1_000), 0)}k`;
	return grNumber(n, 0);
}

export function grInt(n: number | null | undefined): string {
	return grNumber(n, 0);
}

export function pct(n: number | null | undefined, decimals = 1): string {
	if (n === null || n === undefined || Number.isNaN(n)) return '';
	return `${grNumber(n, decimals)}%`;
}

/** ISO date (YYYY-MM-DD…) → DD.MM.YYYY; '' for empty, passthrough otherwise */
export function dmy(d: string | null | undefined): string {
	if (!d) return '';
	const m = /^(\d{4})-(\d{2})-(\d{2})/.exec(d);
	return m ? `${m[3]}.${m[2]}.${m[1]}` : d;
}

/**
 * A histogram bracket label made readable (presentation only): the API's
 * «2000–5000k» is «2–5M», «500–1000k» is «500k–1M», «0–10k» and «>10M»
 * stay as they are. The unit suffix of the API label applies to both ends.
 */
export function bracket(label: string): string {
	const m = label.match(/^(\d+)–(\d+)([kM])$/);
	if (!m) return label;
	const [, lo, hi, unit] = m;
	if (unit !== 'k') return label;
	const a = Number(lo);
	const b = Number(hi);
	const side = (v: number) => (v >= 1000 ? `${v / 1000}M` : `${v}k`);
	if (a >= 1000 && b >= 1000) return `${a / 1000}–${b / 1000}M`;
	if (b >= 1000) return `${side(a)}–${side(b)}`;
	return label;
}
