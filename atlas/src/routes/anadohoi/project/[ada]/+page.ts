import { redirect } from '@sveltejs/kit';
import { apiGet } from '$lib/api';

export interface AnadohoiDecision {
	relation: string;
	detail: string | null;
	excerpt: string | null;
	ada: string;
	kind: string;
	issue_date: string | null;
	subject: string | null;
	org: string | null;
	protocol: string | null;
}

/** the other act of a restatement pair (supersede linkage) */
export interface RestateRef {
	root_ada: string;
	company: string;
	start_date: string | null;
	budget_eur: number | null;
}

export interface AnadohoiProject {
	root_ada: string;
	company: string;
	funder: string | null;
	company_address: string | null;
	works_kind: string | null;
	/** works | study_and_works | study — curated from the act's σκοπός */
	deliverables?: string | null;
	/** digitised works-zone ids (evia_works_zones.geojson) */
	works_zones?: string[] | null;
	/** executing forest co-ops named in the act trail (curated) */
	executors?:
		| { name: string; dase_vat: string | null; ada: string; excerpt: string; note?: string }[]
		| null;
	/** curated θέση-level work locations (full records incl. evidence) */
	work_sites?:
		| {
				name: string;
				kind?: string;
				municipality?: string | null;
				pe?: string | null;
				stremmata?: number | null;
				source_ada: string;
				excerpt: string;
				lat?: number | null;
				lon?: number | null;
				geo_precision?: string | null;
				geo_source?: string | null;
				note?: string | null;
		  }[]
		| null;
	area_stremmata: number | null;
	location_text: string | null;
	municipality: string | null;
	pe: string | null;
	fire_event: string | null;
	budget_eur: number | null;
	budget_current: number | null;
	budget_vat_basis: 'net' | 'gross' | 'unstated' | null;
	budget_net_eur: number | null;
	start_date: string | null;
	deadline_initial: string | null;
	deadline_current: string | null;
	deadline_text: string | null;
	superseded_by: string | null;
	revoked_ada: string | null;
	revoked_date: string | null;
	completed_ada: string | null;
	completed_date: string | null;
	status: string;
	notes: string | null;
	evidence: Record<string, string>;
	decisions: AnadohoiDecision[];
	/** set on a successor: the act this one re-issued (not counted) */
	restates?: RestateRef;
	/** set on a superseded act: the successor that counts instead */
	restated_as?: RestateRef;
}

export const load = async ({ fetch, params }) => {
	const p = await apiGet<AnadohoiProject>(fetch, `/api/anadohoi/project/${params.ada}`);
	// a restated act has ONE canonical page — its successor's, which shows
	// the whole trail; old links and /explore rows land there automatically
	// (encode: a Location header cannot carry raw Greek ΑΔΑ characters)
	if (p.superseded_by)
		redirect(308, `/anadohoi/project/${encodeURIComponent(p.superseded_by)}`);
	return { p };
};
