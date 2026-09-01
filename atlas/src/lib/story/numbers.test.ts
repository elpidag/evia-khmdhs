import { describe, expect, it } from 'vitest';
import { NUMBERS, NUMBER_KEYS } from './numbers';

/**
 * The written text carries its figures as `<Num id="…" />` rather than typed
 * digits (the project's rule: a typed number rots on the next refresh — the
 * author's own storyboard said «253 contracts / €632.14 million» and «Seven
 * chains … 1.5 per cent» when the data already answered 254 and eight/1.7).
 * These tests are what makes that safe — a renamed payload field or a mistyped
 * id fails here instead of silently printing «—» in the middle of a sentence.
 *
 * The content is read through Vite's own raw glob rather than `node:fs`, so the
 * file type-checks under svelte-check with no `@types/node` in the tsconfig.
 */
const RAW = import.meta.glob('/src/content/**/*.md', {
	eager: true,
	query: '?raw',
	import: 'default'
}) as Record<string, string>;

const files = Object.entries(RAW).map(([file, text]) => ({
	file: file.split('/').pop() as string,
	text
}));

const USES = /<Num\s+id="([^"]+)"/g;

describe("the written text's live figures", () => {
	it('finds the content to check', () => {
		expect(files.length).toBeGreaterThan(3);
	});

	it('asks only for figures the registry can supply', () => {
		const missing: string[] = [];
		for (const { file, text } of files) {
			for (const m of text.matchAll(USES)) {
				if (!NUMBER_KEYS.includes(m[1])) missing.push(`${file}: ${m[1]}`);
			}
		}
		expect(missing).toEqual([]);
	});

	it('imports Num wherever it uses one', () => {
		const bad = files
			.filter(({ text }) => USES.test(text) && !text.includes("from '$lib/story/Num.svelte'"))
			.map(({ file }) => file);
		USES.lastIndex = 0;
		expect(bad).toEqual([]);
	});

	it('reads every figure out of the card pages’ payload, formatted for English prose', () => {
		const data = {
			overview: {
				kpis: {
					n_contracts: 254,
					total_eur: 633588292.66,
					n_contractors: 157,
					median_eur: 2100443.31,
					n_coops: 246,
					n_orgs: 48,
					n_units: 99
				}
			}
		};
		expect(NUMBERS['antinero.contracts'](data)).toBe('254');
		expect(NUMBERS['antinero.total'](data)).toBe('€633.59 million');
		expect(NUMBERS['antinero.total1'](data)).toBe('€633.6 million');
		expect(NUMBERS['antinero.median'](data)).toBe('€2.10 million');
		expect(NUMBERS['dase.coops'](data)).toBe('246');
		expect(NUMBERS['dase.orgs'](data)).toBe('48');
		// thousands separated the English way — the site's own eur() is European
		// (1.234.567,50) and belongs in tables and charts, not in a sentence
		expect(NUMBERS['dase.contracts']({ overview: { kpis: { n_contracts: 2004 } } })).toBe('2,004');
		expect(NUMBERS['dase.median']({ overview: { kpis: { median_eur: 5792.44 } } })).toBe('€5,792');
	});

	it("reads the story page's figures from /api/meta — facts, sections, freshness", () => {
		const d = {
			meta: {
				generated: '2026-08-31T22:50:56+00:00',
				antinero: { n_contracts: 254, total_eur: 633588292.66 },
				dase: { n_contracts: 2004, total_eur: 30162069.68 },
				anadohoi: { n_projects: 69, stated_eur: 43284256.85, n_companies: 36 },
				facts: {
					dase_records: 2171,
					dase_pre_window: 7,
					dase_forest_eur: 28500000,
					kh_title_only_n: 8,
					kh_title_only_share: 1.7,
					ana_live_vat_net: 15,
					ana_live_vat_gross: 2,
					ana_live_vat_unstated: 27,
					ana_with_sum: 44,
					ana_without_sum: 25
				}
			}
		};
		expect(NUMBERS['antinero.contracts'](d)).toBe('254');
		expect(NUMBERS['dase.records'](d)).toBe('2,171');
		expect(NUMBERS['dase.contracts'](d)).toBe('2,004');
		expect(NUMBERS['dase.total'](d)).toBe('€30.16 million');
		expect(NUMBERS['dase.total1'](d)).toBe('€30.2 million');
		// small counts are spelled, as the author's prose spells them
		expect(NUMBERS['dase.pre_window'](d)).toBe('seven');
		expect(NUMBERS['kh.title_only_n'](d)).toBe('Eight'); // opens its sentence
		expect(NUMBERS['kh.title_only_share'](d)).toBe('1.7');
		expect(NUMBERS['ana.vat_gross'](d)).toBe('two');
		expect(NUMBERS['ana.companies'](d)).toBe('36');
		expect(NUMBERS['meta.refreshed'](d)).toBe('31 August 2026');
	});

	it('derives the KEY FINDINGS comparisons from the compare payload', () => {
		const d = {
			cmp: {
				antinero: {
					n_contracts: 254,
					n_contractors: 157,
					total_eur: 633588292.66,
					median_eur: 2100443.31
				},
				dase: { n_contracts: 2004, n_coops: 246, total_eur: 30162069.68, median_eur: 5792.44 },
				years: ['2021', '2022', '2023', '2024', '2025', '2026'],
				yearly: { antinero: [0, 40.3e6, 72.7e6, 248404208.24, 193.6e6, 78.6e6] },
				dots: {
					antinero: { eur: [161000, 2.1e6, 11.6e6] },
					dase: { eur: [1000, 5792, 160000, 170000] }
				}
			}
		};
		// 633.59 / 30.16 = 21.01 → «more than 21 times»
		expect(NUMBERS['cmp.value_ratio'](d)).toBe('21');
		// 2004 / 254 = 7.9 → «almost eight times fewer»
		expect(NUMBERS['cmp.count_ratio'](d)).toBe('eight');
		// 3 of 4 co-op contracts sit below the smallest AntiNero value
		expect(NUMBERS['cmp.smaller_share'](d)).toBe('75');
		expect(NUMBERS['antinero.peak_eur'](d)).toBe('€248.4 million');
		expect(NUMBERS['antinero.peak_year'](d)).toBe('2024');
		expect(NUMBERS['antinero.contractors'](d)).toBe('157');
		expect(NUMBERS['dase.median'](d)).toBe('€5,792');
	});

	it('says nothing rather than something wrong when the payload is absent', () => {
		for (const key of NUMBER_KEYS) expect(NUMBERS[key]({})).toBeNull();
	});

	it("reads the sponsored figures from that page's own payload shape", () => {
		const d = {
			o: { kpis: { n_projects: 69, n_companies: 36, n_stated: 44, stated_eur: 43284256.85 } }
		};
		expect(NUMBERS['ana.projects'](d)).toBe('69');
		expect(NUMBERS['ana.companies'](d)).toBe('36');
		expect(NUMBERS['ana.stated_n'](d)).toBe('44');
		expect(NUMBERS['ana.stated_eur'](d)).toBe('€43.28 million');
	});
});
