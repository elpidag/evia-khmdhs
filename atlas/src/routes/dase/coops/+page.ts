import type { PageLoad } from './$types';
import { apiGet } from '$lib/api';

export interface CoopRow {
	vat: string;
	name: string;
	form: string | null;
	is_curated: boolean;
	n_contracts: number;
	n_direct: number;
	n_units: number;
	pct_direct: number | null;
	total_eur: number;
}

export const load: PageLoad = async ({ fetch, url }) => {
	const q = url.searchParams.get('q') ?? '';
	const qs = q ? `?q=${encodeURIComponent(q)}` : '';
	const rows = await apiGet<CoopRow[]>(fetch, `/api/dase/coops${qs}`);
	return { rows, q };
};
