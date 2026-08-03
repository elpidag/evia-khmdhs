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

export interface AnadohoiProject {
	root_ada: string;
	company: string;
	funder: string | null;
	company_address: string | null;
	works_kind: string | null;
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
}

export const load = async ({ fetch, params }) => ({
	p: await apiGet<AnadohoiProject>(fetch, `/api/anadohoi/project/${params.ada}`)
});
