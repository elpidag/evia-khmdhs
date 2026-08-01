import type { PageLoad } from './$types';
import { apiGet } from '$lib/api';

export interface DaseContractRow {
	reference_number: string;
	title: string | null;
	contract_signed_date: string | null;
	contractor_names: string | null;
	organization_name: string | null;
	units_operator_name: string | null;
	total_cost_with_vat: number | null;
}

export const load: PageLoad = async ({ fetch, url }) => {
	const q = url.searchParams.get('q') ?? '';
	const qs = q ? `?q=${encodeURIComponent(q)}` : '';
	const data = await apiGet<{ rows: DaseContractRow[]; total_eur: number }>(
		fetch,
		`/api/dase/contracts${qs}`
	);
	return { ...data, q };
};
