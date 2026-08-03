import type { PageLoad } from './$types';
import { apiGet } from '$lib/api';

export interface ArogiFireSummary {
	fire_id: string;
	label: string;
	year: number;
	pes: string[];
	n_cases: number;
	n_acts: number;
	approved_eur: number;
	dka_eur: number;
	completed: number;
	batch_budget_eur: number;
	press: {
		stream: string;
		date: string | null;
		eur: number | null;
		beneficiaries: number | null;
		cumulative: number;
		url: string;
		quote: string;
	}[];
}

export interface ArogiSummary {
	fires: ArogiFireSummary[];
	unattributed: { n_cases: number; approved_eur: number };
	elga: { year: number; eur: number | null; scope: string; report: string; page: number | null; quote: string }[];
	stats: Record<string, number>;
	as_of: string | null;
}

export const load: PageLoad = async ({ fetch }) => ({
	s: await apiGet<ArogiSummary>(fetch, '/api/arogi/summary')
});
