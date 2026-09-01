/**
 * Live figures for the written text.
 *
 * The project's hard rule is that no data-derived number is ever typed into UI
 * copy — a typed figure rots silently on the next refresh (the author's own
 * draft already said «253 contracts / €632.14 million» a day after the count
 * became 254). So the prose carries `<Num id="…" />` and the digits are read
 * from the page's own payload at render time.
 *
 * A key may name SEVERAL sources, tried in order, because the same figure is
 * quoted on different pages with different payloads: the dataset cards hold
 * their overview under `overview`/`o`, while the story loads the small
 * `/api/meta` and `/api/compare` payloads. Each accessor answers null when its
 * payload is absent, and the chain answers the first real value.
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

/** small counts are spelled out, as the author's prose does */
const WORDS = [
	'zero',
	'one',
	'two',
	'three',
	'four',
	'five',
	'six',
	'seven',
	'eight',
	'nine',
	'ten',
	'eleven',
	'twelve'
];
const spell = (v: number): string => (v < WORDS.length ? WORDS[Math.round(v)] : int(v));
const spellCap = (v: number): string => {
	const s = spell(v);
	return s.charAt(0).toUpperCase() + s.slice(1);
};
/** 1.7 → «1.7» — a share the API already rounded */
const plain = (v: number): string => String(v);
/** 2024 → «2024», never «2,024» */
const year = (v: number): string => String(Math.round(v));

/** whatever the page loaded — every field optional, every accessor null-safe */
interface CmpSide {
	n_contracts?: number;
	n_contractors?: number;
	n_coops?: number;
	n_orgs?: number;
	n_units?: number;
	total_eur?: number;
	median_eur?: number;
}
interface PageData {
	overview?: { kpis?: Record<string, number> };
	o?: { kpis?: Record<string, number> };
	meta?: {
		facts?: Record<string, number>;
		generated?: string;
		antinero?: Record<string, number>;
		dase?: Record<string, number>;
		anadohoi?: Record<string, number>;
	} | null;
	cmp?: {
		antinero?: CmpSide;
		dase?: CmpSide;
		yearly?: { antinero?: number[]; dase?: number[] };
		years?: string[];
		dots?: { antinero?: { eur?: number[] }; dase?: { eur?: number[] } };
	} | null;
	[k: string]: unknown;
}

type Src = (d: PageData) => number | null;
const num = (v: unknown): number | null => (typeof v === 'number' ? v : null);

const kpi =
	(key: string): Src =>
	(d) =>
		num((d.overview?.kpis ?? d.o?.kpis)?.[key]);
const fact =
	(key: string): Src =>
	(d) =>
		num(d.meta?.facts?.[key]);
const metaOf =
	(section: 'antinero' | 'dase' | 'anadohoi', key: string): Src =>
	(d) =>
		num(d.meta?.[section]?.[key]);
const cmpOf =
	(side: 'antinero' | 'dase', key: keyof CmpSide): Src =>
	(d) =>
		num(d.cmp?.[side]?.[key]);

/** the first source that answers, formatted; null when none does */
const from =
	(fmt: (v: number) => string, ...sources: Src[]) =>
	(d: PageData): string | null => {
		for (const s of sources) {
			const v = s(d);
			if (v !== null) return fmt(v);
		}
		return null;
	};

/* derived figures the compare payload carries the ingredients for */

/** Σ AntiNero / Σ co-op stated value, floored — «more than N times» */
const valueRatio: Src = (d) => {
	const a = cmpOf('antinero', 'total_eur')(d);
	const b = cmpOf('dase', 'total_eur')(d);
	return a !== null && b ? Math.floor(a / b) : null;
};
/** co-op contracts per AntiNero contract, rounded — «almost N times fewer» */
const countRatio: Src = (d) => {
	const a = cmpOf('dase', 'n_contracts')(d);
	const b = cmpOf('antinero', 'n_contracts')(d);
	return a !== null && b ? Math.round(a / b) : null;
};
/** % of co-op contracts smaller than the SMALLEST AntiNero contract, floored */
const smallerShare: Src = (d) => {
	const a = d.cmp?.dots?.antinero?.eur;
	const b = d.cmp?.dots?.dase?.eur;
	if (!a?.length || !b?.length) return null;
	const min = Math.min(...a);
	return Math.floor((100 * b.filter((v) => v < min).length) / b.length);
};
/** the biggest AntiNero year's € — and which year that is */
const peak = (d: PageData): { eur: number; year: number } | null => {
	const ys = d.cmp?.yearly?.antinero;
	const labels = d.cmp?.years;
	if (!ys?.length || !labels?.length) return null;
	let best = 0;
	for (let i = 1; i < ys.length; i++) if (ys[i] > ys[best]) best = i;
	return { eur: ys[best], year: Number(labels[best]) };
};

const MONTHS = [
	'January',
	'February',
	'March',
	'April',
	'May',
	'June',
	'July',
	'August',
	'September',
	'October',
	'November',
	'December'
];

/**
 * Every token the written text may use. A key that is asked for and missing
 * fails `numbers.test.ts`, so a renamed payload field cannot quietly blank a
 * sentence.
 */
export const NUMBERS: Record<string, (d: PageData) => string | null> = {
	// AntiNero — the card page's overview, or the story's meta/compare payloads
	'antinero.contracts': from(int, kpi('n_contracts'), metaOf('antinero', 'n_contracts')),
	'antinero.total': from((v) => millions(v), kpi('total_eur'), metaOf('antinero', 'total_eur')),
	'antinero.total1': from(
		(v) => millions(v, 1),
		kpi('total_eur'),
		metaOf('antinero', 'total_eur')
	),
	'antinero.contractors': from(int, kpi('n_contractors'), cmpOf('antinero', 'n_contractors')),
	'antinero.median': from(
		(v) => millions(v),
		kpi('median_eur'),
		cmpOf('antinero', 'median_eur')
	),
	'antinero.peak_eur': (d) => {
		const p = peak(d);
		return p ? millions(p.eur, 1) : null;
	},
	'antinero.peak_year': (d) => {
		const p = peak(d);
		return p ? year(p.year) : null;
	},

	// Forest workers' co-operatives — /dase
	'dase.contracts': from(int, kpi('n_contracts'), metaOf('dase', 'n_contracts')),
	'dase.coops': from(int, kpi('n_coops'), cmpOf('dase', 'n_coops')),
	'dase.total': from((v) => millions(v), kpi('total_eur'), metaOf('dase', 'total_eur')),
	'dase.total1': from((v) => millions(v, 1), kpi('total_eur'), metaOf('dase', 'total_eur')),
	'dase.median': from(euros, kpi('median_eur'), cmpOf('dase', 'median_eur')),
	'dase.orgs': from(int, kpi('n_orgs'), cmpOf('dase', 'n_orgs')),
	'dase.units': from(int, kpi('n_units'), cmpOf('dase', 'n_units')),
	'dase.records': from(int, fact('dase_records')),
	'dase.pre_window': from(spell, fact('dase_pre_window')),
	'dase.forest_eur': from((v) => millions(v, 1), fact('dase_forest_eur')),

	// the title-only tier of the AntiNero sourcing rule
	'kh.title_only_n': from(spellCap, fact('kh_title_only_n')),
	'kh.title_only_share': from(plain, fact('kh_title_only_share')),

	// Financed by private companies — /anadohoi
	'ana.projects': from(int, kpi('n_projects'), metaOf('anadohoi', 'n_projects')),
	'ana.companies': from(int, kpi('n_companies'), metaOf('anadohoi', 'n_companies')),
	'ana.stated_n': from(int, kpi('n_stated'), fact('ana_with_sum')),
	'ana.stated_eur': from(
		(v) => millions(v),
		kpi('stated_eur'),
		metaOf('anadohoi', 'stated_eur')
	),
	'ana.vat_net': from(int, fact('ana_live_vat_net')),
	'ana.vat_gross': from(spell, fact('ana_live_vat_gross')),
	'ana.vat_unstated': from(int, fact('ana_live_vat_unstated')),
	'ana.without_sum': from(int, fact('ana_without_sum')),

	// the comparisons KEY FINDINGS argues from
	'cmp.value_ratio': from(int, valueRatio),
	'cmp.count_ratio': from(spell, countRatio),
	'cmp.smaller_share': from(int, smallerShare),

	// «last refreshed on …», as the records themselves report it
	'meta.refreshed': (d) => {
		const g = d.meta?.generated;
		if (!g) return null;
		const t = new Date(g);
		return `${t.getUTCDate()} ${MONTHS[t.getUTCMonth()]} ${t.getUTCFullYear()}`;
	}
};

export const NUMBER_KEYS = Object.keys(NUMBERS);
