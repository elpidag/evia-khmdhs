/** Typed helpers for the Atlas JSON API (atlas_api, Flask). */
import { browser } from '$app/environment';
import { error } from '@sveltejs/kit';

type Fetch = typeof globalThis.fetch;

export async function apiGet<T>(fetch: Fetch, path: string): Promise<T> {
	const resp = await fetch(path);
	if (!resp.ok) {
		error(resp.status === 404 ? 404 : 502, `API ${path} returned ${resp.status}`);
	}
	return resp.json() as Promise<T>;
}

/**
 * Client-side memoised fetch for the immutable dataset endpoints. The data
 * only changes on a DB refresh, so navigating back to a page must not
 * re-download or re-parse hundreds of KB of JSON. SSR never uses the cache.
 */
const clientCache = new Map<string, Promise<unknown>>();

export function apiGetCached<T>(fetch: Fetch, path: string): Promise<T> {
	if (!browser) return apiGet<T>(fetch, path);
	if (!clientCache.has(path)) {
		clientCache.set(
			path,
			apiGet<T>(fetch, path).catch((e) => {
				clientCache.delete(path); // don't memoise failures
				throw e;
			})
		);
	}
	return clientCache.get(path) as Promise<T>;
}

// ---------------------------------------------------------------- shapes

export interface Meta {
	antinero: { n_contracts: number; total_eur: number; n_payments: number };
	dase?: { n_contracts: number; total_eur: number };
	anadohoi?: { n_projects: number; stated_eur: number };
	/** dataset-state counts cited in prose — computed, never hardcoded */
	facts?: Record<string, number>;
	generated: string | null;
}

export interface Kpis {
	n_contracts: number;
	/** Σ stated values excl. VAT (stated analytics basis) */
	total_eur: number;
	/** Σ stated values excl. VAT */
	stated_eur: number;
	/** Σ non-cancelled payment orders excl. VAT */
	paid_eur: number;
	n_payments: number;
	/** median stated value excl. VAT */
	median_eur: number;
	n_contractors: number;
	n_authorities: number;
	pct_direct: number;
	n_single_bidder: number;
	n_cancelled: number;
}

export interface ProcedureRow {
	label: string;
	n_contracts: number;
	eur: number;
}

export interface TopContractor {
	vat_number: string;
	name: string;
	n_contracts: number;
	total_eur: number;
}

export interface RegionMoney {
	pe: string;
	n_contracts: number;
	n_contractors?: number;
	split_eur: number;
	exposure_eur: number;
}

export interface ContractPoint {
	ref: string;
	title: string;
	authority: string;
	kind: string;
	lat: number;
	lon: number;
	pe: string;
	eff_eur: number;
}

export interface ContractorPoint {
	vat: string;
	name: string;
	lat: number;
	lon: number;
	pe: string | null;
	precision: string;
	n_contracts: number;
	total_eur: number;
}

export interface OverviewContract {
	ref: string;
	title: string;
	eff_eur: number;
	contractors: { vat: string; name: string }[];
	authorities: string[];
	regions: { pe: string; split_eur: number }[];
}

export interface AntineroMapPayload {
	work_regions: RegionMoney[];
	home_regions: RegionMoney[];
	coverage: {
		resolved_eur: number;
		unresolved_eur: number;
		total_eur: number;
		n_contractors_resolved: number;
		n_contractors_total: number;
	};
	contract_points: ContractPoint[];
	contractor_points: {
		points: ContractorPoint[];
		coverage: { n_with_coords: number; n_total: number; unmapped_eur: number };
	};
	contracts: OverviewContract[];
}

export interface PaymentEvent {
	pay: string;
	ref: string;
	d: string | null;
	m: string | null;
	eur: number;
	scope: string;
	credit: number;
}

export interface PaymentsPayload {
	events: PaymentEvent[];
	/** t = trimmed title; y = the contract's signature YEAR (the strip's
	 *  cohort colour, 2026-08-22) */
	contracts: Record<string, { t: string; vats?: string[]; y?: string | null }>;
	/** signature→payment lag medians, computed server-side */
	lag?: {
		n: number;
		median_days: number | null;
		median_first_days: number | null;
		n_contracts: number;
	};
	undated: { n: number; eur: number };
	fallback: number;
}

export interface SankeyPayload {
	nodes: { id: string; label: string; kind: string; n?: number }[];
	links: { s: string; t: string; eur: number }[];
}

export interface SwarmRow {
	ref: string;
	t: string;
	eur: number;
	scope: string;
	year: string | null;
	/** ISO signed date (submission fallback) — the tooltip's DD.MM.YYYY */
	d: string | null;
	proc: 'direct' | 'open' | 'nego' | 'other';
	single_bidder: 0 | 1;
	pe: string | null;
	/** the curated work-type category key */
	category?: string | null;
}

export interface PeYearly {
	pes: { pe: string; total_eur: number; years: Record<string, number> }[];
	years: string[];
	unresolved_eur: number;
}

export interface Histogram {
	labels: string[];
	counts: number[];
	edges: number[];
	median: number;
	n: number;
	total_eur: number;
}

export interface DaseKpis {
	n_contracts: number;
	/** Σ stated values excl. VAT (live population) */
	total_eur: number;
	/** Σ non-cancelled payment orders excl. VAT (partial coverage) */
	paid_eur: number;
	n_paid_contracts: number;
	n_payments: number;
	/** live contracts with >1 contractor */
	n_consortium: number;
	/** worst-case registry spellings of one co-op (canonical ΑΦΜ) */
	max_name_variants: number;
	n_coops: number;
	n_orgs: number;
	n_units: number;
	pct_direct: number;
	median_eur: number;
	p90_eur: number;
	gross_n: number;
	gross_eur: number;
	n_cancelled: number;
	n_superseded: number;
}

/** /api/dase/allocation — the works/seats choropleth duo (2026-08-24):
 *  the same money by where the work is and by where the co-op is seated,
 *  both reconciling to the stated-net basis on the even split */
export interface DaseAllocation {
	work_regions: { pe: string; n: number; eur: number; imported_eur: number }[];
	seat_regions: { pe: string; n_coops: number; eur: number; exported_eur: number }[];
	/** every (seat Π.Ε. → work Π.Ε.) pair; from === to is money that stayed home */
	flows: { from: string; to: string; n: number; eur: number }[];
	unresolved: { n: number; eur: number };
	total_eur: number;
	n_contracts: number;
	n_coops: number;
	away_eur: number;
	local_eur: number;
	away_share: number;
	n_coops_away: number;
	/** one point per located co-operative — the drill's dots */
	coop_points: { vat: string; lat: number; lon: number; pe: string | null; precision: string | null; place: string | null; name: string | null }[];
	/** which co-operatives worked in each work Π.Ε., and for how much */
	region_coops: { pe: string; vat: string; n: number; eur: number }[];
}

export interface DaseOverview {
	kpis: DaseKpis;
	yearly: { year: string; n: number; eur: number }[];
	/** the declared codes rolled up the CPV tree — same shape and
	 *  conventions as the Anti-nero front page's (2026-08-24) */
	cpv_tree?: AntineroOverview['cpv_tree'];
	/** the live direct-award contracts' stated values on the doubling axis;
	 *  NO thresholds by design — the άρθρο 118 ceilings do not govern the
	 *  forest-code / ΠΝΠ regimes (DATA_DECISIONS 2026-08-24) */
	direct_awards?: {
		labels: string[];
		counts: number[];
		edges: number[];
		n: number;
		total_eur: number;
		median: number;
		n_above_30k: number;
		n_above_60k: number;
	};
	top_coops: {
		vat: string;
		name: string;
		form: string | null;
		is_curated: boolean;
		n_contracts: number;
		n_direct: number;
		n_units: number;
		pct_direct: number;
		total_eur: number;
	}[];
	top_orgs: { name: string; n_contracts: number; total_eur: number }[];
	top_units: { name: string; n_contracts: number; total_eur: number }[];
	/** category data: awarding bodies by public-bodies registry kind,
	 *  awarding units by the map's kind vocabulary (dx/dd/muni/misc), and
	 *  the joint body→unit distribution behind the delegation diagram */
	kind_mix: {
		bodies: { kind: string; n: number; eur: number }[];
		units: { kind: string; n: number; eur: number }[];
		flows: { body: string; unit: string; n: number; eur: number }[];
		/** third column of the delegation diagram: the biggest co-ops by €,
		 *  plus one pooled node (vat/label null, carries n_coops) */
		coops: {
			vat: string | null;
			label: string | null;
			n: number;
			eur: number;
			n_coops?: number;
		}[];
		coop_flows: { unit: string; vat: string | null; n: number; eur: number }[];
	};
	procedures: ProcedureRow[];
	types: ProcedureRow[];
	cpvs: { cpv: string; label: string; n_contracts: number; noise: boolean }[];
	histogram: Histogram;
	by_pe: {
		regions: { pe: string; n_contracts: number; eur: number }[];
		unresolved: { n: number; eur: number };
	};
}

export interface DaseMapContract {
	ref: string;
	d: string | null;
	eur: number | null;
	/** the awarding unit (forest circles) or body (per-Π.Ε. circles) */
	by: string;
	/** curated display name(s) of the co-op(s) that won it */
	coop: string;
}

export interface DaseMapPayload {
	/** one circle per awarding forest unit — at its seat, or at the Π.Ε.
	 *  centroid for the few units without a registry seat */
	units: {
		name: string;
		/** 'dx' Δασαρχείο / 'dd' Διεύθυνση Δασών-level body */
		kind: string | null;
		pe: string | null;
		lat: number;
		lon: number;
		n: number;
		eur: number;
		median_eur: number;
		contracts: DaseMapContract[];
	}[];
	/** contracts awarded by non-forest bodies, grouped per Π.Ε. */
	other: {
		pe: string;
		/** 'muni' δήμοι/περιφέρειες + their entities · 'misc' other public bodies */
		kind: 'muni' | 'misc';
		lat: number;
		lon: number;
		n: number;
		eur: number;
		median_eur: number;
		contracts: DaseMapContract[];
	}[];
	unresolved: { n: number; eur: number };
}

export interface DaseSwarm {
	ref: string[];
	t: string[];
	eur: (number | null)[];
	year: (string | null)[];
	/** ISO signed date (submission fallback) — the tooltip's DD.MM.YYYY */
	d: (string | null)[];
	pe: (string | null)[];
	vat: (string | null)[];
}

export interface PipelineEntity {
	vat: string;
	name: string;
	eur: number;
}

export interface Pipelines {
	antinero: { n_vats: number; total_eur: number; entities: PipelineEntity[] };
	dase: { n_vats: number; total_eur: number; entities: PipelineEntity[] };
	dase_n_coops: number;
	vat_overlap: string[];
	shared_awarders: {
		name: string;
		antinero_n: number;
		antinero_eur: number;
		dase_n: number;
		dase_eur: number;
	}[];
}

export interface ComparePayload {
	/** the STATE-FUNDED animation's per-contract dots (2026-08-25) */
	dots: {
		antinero: { ref: string[]; eur: number[]; year: (number | null)[]; total_eur: number };
		dase: { ref: string[]; eur: number[]; year: (number | null)[]; total_eur: number };
	};
	antinero: {
		n_contracts: number;
		total_eur: number;
		n_contractors: number;
		pct_direct: number;
		median_eur: number;
		mean_eur: number;
		n_single_bidder: number;
		n_cancelled: number;
		n_authorities: number;
	};
	dase: DaseKpis & { mean_eur: number };
	ratio: number;
	years: string[];
	yearly: { antinero: number[]; dase: number[] };
	by_pe: {
		pe: string;
		antinero_eur: number;
		antinero_n: number;
		dase_eur: number;
		dase_n: number;
	}[];
	dase_unresolved: { n: number; eur: number };
	hist: {
		edges: number[];
		labels: string[];
		antinero_pct: number[];
		antinero_n: number;
		antinero_median: number;
		dase_pct: number[];
		dase_n: number;
		dase_median: number;
	};
	pipelines: Pipelines;
}

export interface AntineroOverview {
	kpis: Kpis;
	procedures: ProcedureRow[];
	histogram: { edges: number[]; counts: number[]; labels: string[]; median: number };
	/** pure-doubling brackets shared by the dots/brackets CONTRACT VALUES
	 *  frame — same convention as the ΔΑΣΕ chart (user, 2026-08-20) */
	value_histogram: { edges: number[]; counts: number[]; labels: string[]; median: number };
	direct_awards: {
		labels: string[];
		counts: number[];
		edges: number[];
		n: number;
		total_eur: number;
		thresholds: number[];
	};
	timeseries: { months: string[]; series: Record<string, number[]> };
	yearly: { year: string; paid_eur: number; stated_eur: number; total_eur: number }[];
	studies: {
		summary: {
			n_with: number;
			n_in_scope: number;
			total_eur: number;
			net_stated_total: number;
			median_share: number;
		};
		top: {
			ref: string;
			title: string;
			eur: number;
			src_ref: string;
			eff_eur: number;
			share: number;
		}[];
		/** every stated fee against its contract's value (the scatter) */
		points?: { ref: string; s: number; c: number | null; share: number | null; t: string; cat?: string | null }[];
		/** the four honest classes over the 245 (2026-08-22) */
		classes?: { stated: number; db_unstated: number; works_none: number; study_only: number };
	};
	top_contractors: TopContractor[];
	/** the same money attributed to the firms BEHIND the joint ventures
	 *  (DATA_DECISIONS 2026-08-20) — identical population, identical total */
	member_firms: (TopContractor & {
		via_eur: number;
		n_ventures: number;
		is_venture: boolean;
	})[];
	/** what the member view rests on, computed, never hardcoded */
	consortiums: {
		n: number;
		n_documented: number;
		n_firms: number;
		eur: number;
		/** € in ventures whose members no document names — identical in both views */
		eur_unsplit: number;
	};
	top_authorities: Record<string, unknown>[];
	top_signers: Record<string, unknown>[];
	coverage: Record<string, number>;
	/** chains kept in the dataset but excluded from every calculation:
	 *  probably Anti-nero, RRF-16849 membership unproven (chain tips) */
	probable: {
		n: number;
		total_eur: number;
		rows: { ref: string; title: string; d: string | null; eur: number | null }[];
	};
	/** every CPV code declared on an in-scope contract (registry
	 *  description, distinct-contract count) — no € per code: contracts
	 *  declare several codes each */
	cpvs: { code: string; desc: string; n: number }[];
	/** the declared codes rolled up the CPV tree: division → class → code,
	 *  distinct-contract counts that OVERLAP (2026-08-23) */
	cpv_tree?: {
		divisions: {
			code: string;
			name_en: string;
			name_el: string;
			n: number;
			classes: {
				code: string;
				name_en: string;
				name_el: string;
				n: number;
				codes: { code: string; name_en: string; name_el: string; n: number }[];
			}[];
		}[];
		n_contracts: number;
		n_codes: number;
		codes_per_contract: number;
	};
	/** curated work-type category per in-scope contract (ONE each, so the
	 *  stated-net sums reconcile to the programme total) */
	categories: {
		key: string;
		label: string;
		/** English label + the works this category's contracts NAME (themes) */
		label_en?: string;
		n: number;
		eur: number;
		/** contracts of this category naming at least one work */
		n_named?: number;
		names?: { theme: string; label_en: string; label_el: string; n: number }[];
	}[];
	/** the works the contracts name — the multi-label themes, counted in contracts; the unspecified ones apart */
	/** study / study_and_works / works — the 1-2-3 scope model (2026-08-22) */
	deliverables?: { study?: number; study_and_works?: number; works?: number };
	themes: {
		themes: { theme: string; label_en: string; label_el: string; n: number }[];
		/** the combination of works each title names, counted (the bundles) */
		bundles?: { themes: string[]; n: number }[];
		unspecified: number;
		n_contracts: number;
		n_named: number;
	};
	/** what KIND of σύμβαση each in-scope record is — all of them are
	 *  συμβάσεις, the kind says which (original, revision of terms,
	 *  supplementary contract or works, deadline extension) */
	document_kinds: {
		total: number;
		counts: Record<string, number>;
		labels: Record<string, { el: string; en: string }>;
	};
}

export interface ExploreRow {
	ds: 'antinero' | 'dase' | 'anadohoi';
	ref: string;
	d: string | null;
	t: string;
	co: string;
	/** registry spellings the curated display name replaced — searchable */
	ac?: string[];
	/** stated value net of ΦΠΑ (anadohoi: committed, net where stated) */
	v: number | null;
	pe: string[];
	hq: string[];
	proc: 'direct' | 'open' | 'nego' | 'other' | 'sponsor';
	st: string | null;
	b1: number;
	/** linked διακήρυξη/πρόσκληση: 1/0 for Anti-nero, null elsewhere */
	pr: number | null;
	/** project end date on record: 1/0 (Anti-nero completion act /
	 *  anadohoi completed status), null for ΔΑΣΕ (never harvested) */
	fin: number | null;
	/** last date of the contract's chain, when it has more than one record —
	 *  the row's date cell reads «first → last» (Anti-nero only) */
	d1?: string;
	/** every record of the chain, oldest first: what each one IS, when, and
	 *  the value it carried. Absent for a contract posted once. */
	vs?: { ref: string; d: string | null; k: string | null; v: number | null }[];
	/** the chain's other ΑΔΑΜ — searchable, so citing an earlier version
	 *  finds the contract instead of nothing */
	alt?: string[];
	/** the δήμοι the contract's documents name (Anti-nero only; absent for
	 *  the 93 that name none, and for the other two datasets) */
	mu?: string[];
}

export interface ExplorePayload {
	rows: ExploreRow[];
	counts: Record<string, number>;
}

/** `/api/connections` — the Anti-nero flow layer (region→region flows, the
 *  local-vs-imported split, hubs, signers, consortium pairs). Fetched by the
 *  front page's FLOWS OF MONEY frame post-hydration; the old /connections
 *  page that first carried it left the site on 2026-08-23. */
export interface Connections {
	contractor_authority: { vat: string; auth: string; n: number; eur: number }[];
	contractor_pe: { vat: string; pe: string; n: number; eur: number }[];
	contractor_signer: { vat: string; signer: string; n: number; eur: number }[];
	flows: { source_pe: string; target_pe: string; n_contracts: number; total_eur: number }[];
	/** the same flows with a signature-year dimension — Σ over years == flows */
	flows_yearly: {
		source_pe: string;
		target_pe: string;
		year: string;
		n_contracts: number;
		total_eur: number;
	}[];
	origins: {
		target_pe: string;
		n_contracts: number;
		total_eur: number;
		local_eur: number;
		imported_eur: number;
		unknown_eur: number;
	}[];
	pairs: { a: string; b: string; refs: string[]; eur: number }[];
	contractors: Record<string, { name: string; home_pe: string | null; eur: number }>;
	authorities: Record<string, { pe: string; kind: string; lat: number; lon: number }>;
	coverage: {
		resolved_eur: number;
		unresolved_eur: number;
		total_eur: number;
	};
}
