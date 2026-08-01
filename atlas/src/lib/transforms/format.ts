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

export function grInt(n: number | null | undefined): string {
	return grNumber(n, 0);
}

export function pct(n: number | null | undefined, decimals = 1): string {
	if (n === null || n === undefined || Number.isNaN(n)) return '';
	return `${grNumber(n, decimals)}%`;
}
