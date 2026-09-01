/**
 * Live figures for the written text.
 *
 * The project's hard rule is that no data-derived number is ever typed into UI
 * copy — a typed figure rots silently on the next refresh (the author's own
 * draft already said «253 contracts / €632.14 million» a day after the count
 * became 254). So the prose carries `<Num id="…" />` and the digits are read
 * from the page's own payload at render time.
 *
 * FORMATTING IS ENGLISH PROSE, deliberately: «2,004 contracts» and «€633.59
 * million» are what an English sentence wants. The site's own `eur()`/`grInt()`
 * are European (1.234.567,50) and belong in tables, charts and facts rows.
 */

/** 2004 → «2,004» */
const int = (v: number): string => Math.round(v).toLocaleString('en-GB');

/** 633588292.66 → «€633.59 million» */
const millions = (v: number, decimals = 2): string =>
	`€${(v / 1_000_000).toLocaleString('en-GB', {
		minimumFractionDigits: decimals,
		maximumFractionDigits: decimals
	})} million`;

/** 5792.44 → «€5,792» */
const euros = (v: number): string => `€${Math.round(v).toLocaleString('en-GB')}`;

/** whatever the page loaded: the card pages hold their overview payload here */
interface PageData {
	overview?: { kpis?: Record<string, number> };
	o?: { kpis?: Record<string, number> };
	meta?: { facts?: Record<string, number> } | null;
	[k: string]: unknown;
}

const kpi =
	(key: string, fmt: (v: number) => string) =>
	(d: PageData): string | null => {
		const k = d.overview?.kpis ?? d.o?.kpis;
		const v = k?.[key];
		return typeof v === 'number' ? fmt(v) : null;
	};

/**
 * Every token the written text may use. A key that is asked for and missing
 * fails `numbers.test.ts`, so a renamed payload field cannot quietly blank a
 * sentence.
 */
export const NUMBERS: Record<string, (d: PageData) => string | null> = {
	// AntiNero — /antinero's own overview payload
	'antinero.contracts': kpi('n_contracts', int),
	'antinero.total': kpi('total_eur', (v) => millions(v)),
	'antinero.contractors': kpi('n_contractors', int),
	'antinero.median': kpi('median_eur', (v) => millions(v)),

	// Forest workers' co-operatives — /dase
	'dase.contracts': kpi('n_contracts', int),
	'dase.coops': kpi('n_coops', int),
	'dase.total': kpi('total_eur', (v) => millions(v)),
	'dase.median': kpi('median_eur', euros),
	'dase.orgs': kpi('n_orgs', int),
	'dase.units': kpi('n_units', int),

	// Financed by private companies — /anadohoi
	'ana.projects': kpi('n_projects', int),
	'ana.companies': kpi('n_companies', int),
	'ana.stated_n': kpi('n_stated', int),
	'ana.stated_eur': kpi('stated_eur', (v) => millions(v))
};

export const NUMBER_KEYS = Object.keys(NUMBERS);
