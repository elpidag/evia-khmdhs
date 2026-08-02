import type { PageLoad } from './$types';
import { apiGet } from '$lib/api';

export interface ContractDetail {
	reference_number: string;
	title: string | null;
	contract_signed_date: string | null;
	start_date: string | null;
	end_date: string | null;
	cancelled: number;
	cancellation_reason: string | null;
	organization_name: string | null;
	units_operator_name: string | null;
	signer_name: string | null;
	procedure_type: string | null;
	award_procedure: string | null;
	contract_type: string | null;
	legal_context: string | null;
	public_funding_ref: string | null;
	notice_reference_number: string | null;
	prev_reference_no: string | null;
	next_reference_no: string | null;
	bids_submitted: number | null;
	contract_duration: number | null;
	contract_duration_unit: string | null;
	total_cost_with_vat: number | null;
	total_cost_without_vat: number | null;
	paid_with_vat: number | null;
	paid_without_vat: number | null;
	effective_cost_with_vat: number | null;
	scope: { scope: string; in_scope: number; superseded_by: string | null } | null;
	contractors: { vat_number: string; name: string; country: string | null }[];
	cpvs: { cpv_code: string; cpv_description: string | null }[];
	nuts: { nuts_code: string; nuts_name: string | null }[];
	objects: {
		quantity: number | null;
		unit_type: string | null;
		cost_without_vat: number | null;
		vat_percent: number | null;
		short_description: string | null;
	}[];
	payments: {
		payment_ref: string;
		signed_date: string | null;
		title: string | null;
		amount_with_vat: number | null;
		cancelled: number;
		credit: number;
		ada: string | null;
		correction_note: string | null;
	}[];
	regions: { region_pe: string; source: string | null; note: string | null }[];
	sites: { site_name: string; region_pe: string; page: number | null; excerpt: string | null }[];
	timeline: {
		adam: string;
		kind: 'request' | 'approved_request' | 'notice' | 'auction' | 'contract' | 'completion';
		title: string | null;
		d: string | null;
		cancelled: number;
		in_db: boolean;
		/** completion acts only (Diavgeia) */
		ckind?: 'oristiki_paralavi' | 'peraiosi' | 'oloklirosi';
		end_basis?: 'protocol_date' | 'act_date';
		end_excerpt?: string | null;
	}[];
}

export const load: PageLoad = async ({ fetch, params }) => {
	return {
		c: await apiGet<ContractDetail>(fetch, `/api/antinero/contract/${params.adam}`)
	};
};
