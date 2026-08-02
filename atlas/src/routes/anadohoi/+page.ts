import { apiGet } from '$lib/api';

export interface AnadohoiOverviewProject {
	ada: string;
	company: string;
	funder: string | null;
	works_kind: string | null;
	area: number | null;
	pe: string | null;
	fire: string | null;
	budget: number | null;
	budget_stated: number | null;
	start: string | null;
	deadline0: string | null;
	deadline: string | null;
	dtext: string | null;
	completed: string | null;
	revoked: string | null;
	status: string;
	amendments: { ada: string; date: string | null }[];
	superseded_by: string | null;
	location: string | null;
}

export interface AnadohoiOverview {
	kpis: {
		n_projects: number;
		n_companies: number;
		stated_eur: number;
		n_stated: number;
		area_stremmata: number;
		statuses: Record<string, number>;
		status_as_of: string | null;
	};
	projects: AnadohoiOverviewProject[];
	fires: {
		fire: string;
		n: number;
		completed: number;
		budget: number;
		first_start: string | null;
	}[];
	sponsors: { company: string; n: number; budget: number; unstated: number }[];
	monthly: { m: string; n: number }[];
}

export const load = async ({ fetch }) => ({
	o: await apiGet<AnadohoiOverview>(fetch, '/api/anadohoi/overview')
});
