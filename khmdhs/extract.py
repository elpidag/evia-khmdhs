"""Pure functions that transform the API JSON into rows for the SQLite tables.

No I/O, no external dependencies — easy to unit-test by feeding example dicts.
"""
from __future__ import annotations

import json
from datetime import datetime, timezone
from typing import Any


def _kv(d: dict | None, key: str) -> tuple[str | None, str | None]:
    """Return (key, value) from a `{"key": ..., "value": ...}` field, or (None, None)."""
    if not isinstance(d, dict):
        return None, None
    sub = d.get(key)
    if not isinstance(sub, dict):
        return None, None
    return sub.get("key"), sub.get("value")


def _bool_int(v: Any) -> int | None:
    if v is None:
        return None
    return 1 if bool(v) else 0


def parent_row(item: dict) -> dict:
    """Flatten one API contract record into a `contracts` table row."""
    cdd = item.get("contractingDataDetails") or {}
    funding = item.get("fundingDetails") or {}

    procedure_code, procedure_value = _kv(item, "procedureType")
    award = item.get("awardProcedure")
    award_value = award.get("value") if isinstance(award, dict) else award
    assign_value = (item.get("assignCriteria") or {}).get("value")
    contract_type_code, contract_type_value = _kv(item, "contractType")
    legal_value = (item.get("legalContext") or {}).get("value")
    nuts_code, nuts_region = _kv(item, "nutsCode")
    nuts_country = (item.get("nutsCountry") or {}).get("value")
    org_code, org_name = _kv(item, "organization")
    type_auth = (item.get("typeOfContractingAuthority") or {}).get("value")
    auth_activity = (item.get("contractingAuthorityActivity") or {}).get("value")
    central = (item.get("centralGovernmentAuthority") or {}).get("value")
    units_code, units_name = _kv(cdd, "unitsOperator")
    signer_code, signer_name = _kv(cdd, "signers")
    duration_unit = (item.get("contractDurationUnitOfMeasure") or {}).get("value")

    auction_refs = item.get("auctionRefNo") or []
    next_refs = item.get("nextRefNo") or []

    return {
        "reference_number": item.get("referenceNumber"),
        "title": item.get("title"),
        "contract_number": item.get("contractNumber"),
        "contract_signed_date": item.get("contractSignedDate"),
        "submission_date": item.get("submissionDate"),
        "last_update_date": item.get("lastUpdateDate"),
        "start_date": item.get("startDate"),
        "end_date": item.get("endDate"),
        "no_end_date": _bool_int(item.get("noEndDate")),
        "cancelled": _bool_int(item.get("cancelled")),
        "cancellation_date": item.get("cancellationDate"),
        "cancellation_reason": item.get("cancellationReason"),
        "organization_code": org_code,
        "organization_name": org_name,
        "organization_vat": item.get("organizationVatNumber"),
        "type_of_contracting_authority": type_auth,
        "contracting_authority_activity": auth_activity,
        "central_government_authority": central,
        "units_operator_code": units_code,
        "units_operator_name": units_name,
        "signer_code": signer_code,
        "signer_name": signer_name,
        "procedure_type_code": procedure_code,
        "procedure_type": procedure_value,
        "award_procedure": award_value,
        "assign_criteria": assign_value,
        "contract_type_code": contract_type_code,
        "contract_type": contract_type_value,
        "legal_context": legal_value,
        "nuts_code": nuts_code,
        "nuts_region_name": nuts_region,
        "nuts_city": item.get("nutsCity"),
        "nuts_postal_code": item.get("nutsPostalCode"),
        "nuts_country": nuts_country,
        "total_cost_without_vat": item.get("totalCostWithoutVAT"),
        "total_cost_with_vat": item.get("totalCostWithVAT"),
        "contract_budget": item.get("contractBudget"),
        "bids_submitted": item.get("bidsSubmitted"),
        "max_bids_submitted": item.get("maxBidsSubmitted"),
        "number_of_sections": item.get("numberOfSections"),
        "contract_duration": item.get("contractDuration"),
        "contract_duration_unit": duration_unit,
        "public_funding_ref": funding.get("publicFundingRef"),
        "public_funding_ref_num": funding.get("publicFundingRefNum"),
        "public_funding_ref_ops": funding.get("publicFundingRefOps"),
        "cofund_program_ref": funding.get("cofundProgramRef"),
        "espa_fund_program_ref": funding.get("espaFundProgramRef"),
        "notice_reference_number": item.get("noticeReferenceNumber") or (auction_refs[0] if auction_refs else None),
        "prev_reference_no": item.get("prevReferenceNo"),
        "next_reference_no": next_refs[0] if next_refs else None,
        "raw_json": json.dumps(item, ensure_ascii=False),
        "fetched_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
    }


def child_rows(adam: str, item: dict) -> dict[str, list[tuple]]:
    """Return rows for the contractors / cpvs / nuts / objects child tables."""
    cdd = item.get("contractingDataDetails") or {}
    members = cdd.get("contractingMembersDataList") or []

    contractors: list[tuple] = []
    for i, m in enumerate(members):
        if not isinstance(m, dict):
            continue
        country = (m.get("country") or {}).get("value")
        contractors.append(
            (adam, i, m.get("vatNumber"), m.get("name"), country, _bool_int(m.get("greekVatNumber")))
        )

    cpvs: list[tuple] = []
    objects: list[tuple] = []
    seen_cpv: set[str] = set()
    for j, obj in enumerate(item.get("objectDetailsList") or []):
        if not isinstance(obj, dict):
            continue
        unit_type = (obj.get("type") or {}).get("value")
        currency = (obj.get("currency") or {}).get("value")
        objects.append((
            adam, j,
            obj.get("quantity"),
            unit_type,
            obj.get("costWithoutVAT"),
            obj.get("vat"),
            currency,
            obj.get("shortDescription"),
        ))
        for cpv in obj.get("cpvs") or []:
            if not isinstance(cpv, dict):
                continue
            code = cpv.get("key")
            if code and code not in seen_cpv:
                seen_cpv.add(code)
                cpvs.append((adam, len(cpvs), code, cpv.get("value")))

    nuts_rows: list[tuple] = []
    for k, n in enumerate(item.get("nutsCodes") or []):
        if not isinstance(n, dict):
            continue
        nc = n.get("nutsCode") if isinstance(n.get("nutsCode"), dict) else None
        if nc:
            nuts_rows.append((adam, k, nc.get("key"), nc.get("value")))

    return {
        "contractors": contractors,
        "contract_cpvs": cpvs,
        "contract_nuts": nuts_rows,
        "contract_objects": objects,
    }
