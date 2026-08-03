import type { PageLoad } from './$types';
import { apiGet } from '$lib/api';

export interface ArogiAct {
	ada: string;
	kind: string;
	issue_date: string | null;
	org: string | null;
	subject: string | null;
	ss_total_eur: number | null;
	ss_excerpt: string | null;
	dka_eur: number | null;
	loan_eur: number | null;
	fire_excerpt: string | null;
}

export interface ArogiCase {
	kind: 'case' | 'batch';
	case_key?: string;
	ada?: string;
	fire_id: string | null;
	fire_label: string | null;
	pe?: string | null;
	n_acts?: number;
	first_date?: string | null;
	last_date?: string | null;
	approved_eur?: number | null;
	dka_eur?: number | null;
	loan_eur?: number | null;
	status?: string;
	budget_eur?: number | null;
	label?: string | null;
	quote?: string | null;
	acts?: ArogiAct[];
}

export const load: PageLoad = async ({ fetch, params }) => ({
	c: await apiGet<ArogiCase>(fetch, `/api/arogi/case/${encodeURIComponent(params.key)}`)
});
