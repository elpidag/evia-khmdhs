import { describe, expect, it } from 'vitest';
import { BLOCKS } from './content';
import { FIGURES } from './figures';
import { ALERTS_CREDIT } from '$lib/transforms/alerts';

describe("the story's live figures", () => {
	const markers = new Map(BLOCKS.filter((b) => b.figure).map((b) => [b.figure!.n, b.figure!.name]));

	it("are keyed by one of the author's own figure numbers", () => {
		expect(Object.keys(FIGURES).length).toBeGreaterThan(0);
		for (const n of Object.keys(FIGURES).map(Number)) {
			expect(markers.has(n), `figure ${n}`).toBe(true);
		}
	});

	it("were built for the marker that carries their number", () => {
		for (const [n, f] of Object.entries(FIGURES)) {
			expect(markers.get(Number(n)), `figure ${n}`).toBe(f.name);
		}
	});

	it('the alerts map is Figure 04, its attributions kept for the sources', () => {
		expect(FIGURES[4].name).toBe('112 emergency alerts');
		// no credit under the figure (the author, 2026-09-04) — the text the
		// licences require is still held for the SOURCES section
		expect(FIGURES[4].credit).toBeUndefined();
		expect(ALERTS_CREDIT).toContain('EOxCloudless');
		expect(ALERTS_CREDIT).toContain('Copernicus Sentinel data 2020');
		expect(ALERTS_CREDIT).toContain('VNP64A1');
		expect(ALERTS_CREDIT).toContain('112Greece');
	});

	it('the CONTRACT TYPE bars are Figure 10, in a slot of their own height', () => {
		expect(FIGURES[10].name).toBe('types of work graph');
		expect(FIGURES[10].frame).toBe('auto');
		expect(FIGURES[10].credit).toBeUndefined();
	});
});
