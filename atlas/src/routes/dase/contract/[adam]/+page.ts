import type { PageLoad } from './$types';
import { apiGet } from '$lib/api';
import type { ContractDetail } from '../../../antinero/contract/[adam]/+page';

export const load: PageLoad = async ({ fetch, params }) => {
	return {
		c: await apiGet<Omit<ContractDetail, 'regions' | 'sites'>>(
			fetch,
			`/api/dase/contract/${params.adam}`
		)
	};
};
