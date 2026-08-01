import type { PageLoad } from './$types';
import { apiGet } from '$lib/api';

export interface ContractRow {
	reference_number: string;
	title: string | null;
	contract_signed_date: string | null;
	contractor_names: string | null;
	regions: string | null;
	scope: string | null;
	total_cost_with_vat: number | null;
	stated_cost_with_vat: number | null;
	n_payments: number;
	bids_submitted: number | null;
	cancelled: number;
}

export const load: PageLoad = async ({ fetch, url }) => {
	const q = url.searchParams.get('q') ?? '';
	const qs = q ? `?q=${encodeURIComponent(q)}` : '';
	const data = await apiGet<{ rows: ContractRow[]; total_eur: number }>(
		fetch,
		`/api/antinero/contracts${qs}`
	);
	return { ...data, q };
};
