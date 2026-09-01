import { describe, expect, it } from 'vitest';
import { BLOCKS } from './content';
import { FIGURES } from './figures';

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

	it('the alerts map is Figure 04, with its attributions', () => {
		expect(FIGURES[4].name).toBe('112 emergency alerts');
		expect(FIGURES[4].credit).toContain('EOxCloudless');
		expect(FIGURES[4].credit).toContain('Copernicus Sentinel data 2020');
		expect(FIGURES[4].credit).toContain('VNP64A1');
		expect(FIGURES[4].credit).toContain('112Greece');
	});
});
