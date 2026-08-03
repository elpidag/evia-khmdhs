import type { PageLoad } from './$types';
import { apiGet } from '$lib/api';

export interface ArogiRow {
	id: string;
	kind: 'case' | 'batch';
	d: string | null;
	d2: string | null;
	fire: string | null;
	fire_id: string | null;
	pe: string | null;
	n: number;
	/** Σ.Σ. approved € (net basis of the acts) or batch budget € */
	v: number | null;
	dka: number | null;
	loan: number | null;
	st: string;
}

export interface ArogiExplore {
	rows: ArogiRow[];
	counts: Record<string, number>;
	fires: { fire_id: string; label: string; year: number }[];
}

export const load: PageLoad = async ({ fetch }) => ({
	o: await apiGet<ArogiExplore>(fetch, '/api/arogi/explore')
});
