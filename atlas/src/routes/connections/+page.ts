import type { PageLoad } from './$types';
import { apiGet } from '$lib/api';

export interface Connections {
	contractor_authority: { vat: string; auth: string; n: number; eur: number }[];
	contractor_pe: { vat: string; pe: string; n: number; eur: number }[];
	contractor_signer: { vat: string; signer: string; n: number; eur: number }[];
	flows: { source_pe: string; target_pe: string; n_contracts: number; total_eur: number }[];
	/** the same flows with a signature-year dimension — Σ over years == flows */
	flows_yearly: {
		source_pe: string;
		target_pe: string;
		year: string;
		n_contracts: number;
		total_eur: number;
	}[];
	origins: {
		target_pe: string;
		n_contracts: number;
		total_eur: number;
		local_eur: number;
		imported_eur: number;
		unknown_eur: number;
	}[];
	pairs: { a: string; b: string; refs: string[]; eur: number }[];
	contractors: Record<string, { name: string; home_pe: string | null; eur: number }>;
	authorities: Record<string, { pe: string; kind: string; lat: number; lon: number }>;
	coverage: {
		resolved_eur: number;
		unresolved_eur: number;
		total_eur: number;
	};
}

export const load: PageLoad = async ({ fetch }) => {
	return { net: await apiGet<Connections>(fetch, '/api/connections') };
};
