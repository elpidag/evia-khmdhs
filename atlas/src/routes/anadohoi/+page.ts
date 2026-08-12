import { apiGet } from '$lib/api';

export interface AnadohoiOverviewProject {
	ada: string;
	company: string;
	/** merged sponsor-group display name (rename/script variants unified) */
	group?: string;
	/** digitised works-zone ids (evia_works_zones.geojson) */
	works_zones?: string[] | null;
	/** executing forest co-ops named in the act trail (curated) */
	executors?:
		| { name: string; dase_vat: string | null; ada: string; excerpt: string; note?: string }[]
		| null;
	funder: string | null;
	works_kind: string | null;
	area: number | null;
	pe: string | null;
	fire: string | null;
	/** net where the act states it (curated VAT basis), else as written */
	budget: number | null;
	budget_stated: number | null;
	vat_basis: 'net' | 'gross' | 'unstated' | null;
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
		/** Σ committed, net where the act states it */
		stated_eur: number;
		median_eur: number;
		n_stated: number;
		vat_counts: Record<'net' | 'gross' | 'unstated', number>;
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
