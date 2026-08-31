# Notes on particular charts — archived, not published

Written on 2026-08-29 to carry the chart caveats whose subject the methodology's
four sections do not cover, and removed from the page the same day (author: «I do
not think any of those are particularly important»). Kept because the rules are
real and may be wanted later; `{names}` were figures computed from `/api/meta`.

## What a ΚΗΜΔΗΣ σύμβαση record is

Original contracts, revisions of terms, supplementary contracts and ministerial approvals are all published under a single record type, whose «type» field describes the object of the contract rather than the nature of the act. Each record was therefore classified from its own heading: {kh_doc_contract} original contracts, {kh_doc_amendment} revisions of terms, {kh_doc_supplementary_contract} supplementary contracts, {kh_doc_approval_ape_supplementary} approvals of supplementary works and {kh_doc_approval_schedule_extension} approvals of an extended deadline. Counted once at its final version, the {kh_records} records correspond to {kh_contracts} contracts.

## Work-type categories

Each contract carries one category, read from the descriptive project title inside the signed document, since the registry title usually names the lot rather than the work; the CPV code serves only as a tie breaker. The vocabulary contains {kh_categories} categories, and further works named in a title are shown separately.

## The timeline on a contract page

The bar is what the contract promised: signature to the deadline it announced, read from the signed text for {kh_deadline_document} contracts rather than from the registry field. Extensions come from the acts that granted them, a tick marks an act of final acceptance, and each € mark is a payment order.

## Procurement families

The call a contract was awarded under is read from the contract's own text, because the registry's chain declares an upstream act for only {kh_family_declared} of the contracts in scope. The front page draws one star per call with the contracts it produced around it.

## Payment orders and the disbursement curve

{kh_payments_n} payment orders are matched to the contracts they pay through the clearance act that authorised each one. The cumulative curve therefore plots money paid rather than money contracted.

## Payment dates

A payment is placed on the date the registry records for it, or on the date of its Diavgeia clearance where it exists only there. Payments whose date cannot be established are shown in a bucket of their own.

## CPV codes

Codes are shown as declared and rolled up through the official CPV 2008 classification. A contract usually declares several, so counts at each level overlap and are never added together.

## The insurance code on logging contracts

An insurance code appears on {dase_cpv_noise} live cooperative contracts. It records no insurance purchased: it tags the employer's social security component of the price, which the State bears as the exploiter of the forest.

## Forest authorities

Contracts are linked to the Διευθύνσεις Δασών and Δασαρχεία named in their titles and itemised objects, against a curated registry of {n_authorities} services and their seats. Where title and objects disagree, the signed document decides.

## The Explore table

On the AntiNero side one row is one contract chain, so a contract amended three times appears once and answers to any of its document numbers. Values are shown on each dataset's own basis and never added across datasets.

## Comparing the two contract datasets

Both sides are compared on stated values excluding VAT. The populations are not symmetrical: one is a single programme, the other every public contract won by a forest workers' cooperative anywhere in the country.

## The zero overlap between the two contract datasets

No tax number appears in both contract datasets. The comparison is made on canonicalised numbers, so that spelling variants and padded zeros cannot conceal a match.
