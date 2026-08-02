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
	generated: string | null;
}

export interface Kpis {
	n_contracts: number;
	total_eur: number;
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
	contracts: Record<string, { t: string; vats?: string[] }>;
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
	proc: 'direct' | 'open' | 'nego' | 'other';
	single_bidder: 0 | 1;
	pe: string | null;
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
	total_eur: number;
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

export interface DaseOverview {
	kpis: DaseKpis;
	yearly: { year: string; n: number; eur: number }[];
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
	procedures: ProcedureRow[];
	types: ProcedureRow[];
	cpvs: { cpv: string; label: string; n_contracts: number; noise: boolean }[];
	histogram: Histogram;
	by_pe: {
		regions: { pe: string; n_contracts: number; eur: number }[];
		unresolved: { n: number; eur: number };
	};
}

export interface DaseSwarm {
	ref: string[];
	t: string[];
	eur: (number | null)[];
	year: (string | null)[];
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
	};
	top_contractors: TopContractor[];
	top_authorities: Record<string, unknown>[];
	top_signers: Record<string, unknown>[];
	coverage: Record<string, number>;
}

export interface ExploreRow {
	ds: 'antinero' | 'dase' | 'anadohoi';
	ref: string;
	d: string | null;
	t: string;
	co: string;
	v: number | null;
	vn: number | null;
	pe: string[];
	hq: string[];
	proc: 'direct' | 'open' | 'nego' | 'other' | 'sponsor';
	st: string | null;
	b1: number;
}

export interface ExplorePayload {
	rows: ExploreRow[];
	counts: Record<string, number>;
}
