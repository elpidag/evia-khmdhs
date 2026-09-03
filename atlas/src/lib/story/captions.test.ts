import { describe, expect, it } from 'vitest';
import { CAPTIONS, captionFor, renderCaption } from './captions';
import { FIGURE_IMAGES } from './figureImages';
import { BLOCKS } from './content';

describe("the story figures' captions", () => {
	const markers = new Map(BLOCKS.filter((b) => b.figure).map((b) => [b.figure!.n, b.figure!.name]));

	it("keys every entry to one of the author's own figure markers", () => {
		expect(CAPTIONS.size).toBeGreaterThan(0);
		for (const key of CAPTIONS.keys()) {
			const n = Number(/^\d+/.exec(key)![0]);
			expect(markers.has(n), `caption ${key}`).toBe(true);
		}
	});

	it('answers for every figure the author has marked', () => {
		for (const n of markers.keys()) {
			expect(captionFor(n, 'a'), `figure ${n}`).not.toBeNull();
		}
	});

	it('gives each image of a multi-image figure its own slot', () => {
		for (const [n, cfg] of Object.entries(FIGURE_IMAGES)) {
			if (cfg.kind === 'single') continue;
			// a carousel or the grid: slots a and b must both resolve
			expect(captionFor(Number(n), 'a'), `figure ${n}a`).not.toBeNull();
			expect(captionFor(Number(n), 'b'), `figure ${n}b`).not.toBeNull();
		}
	});

	it('falls back from a slide to the figure, and reports nothing honestly', () => {
		// figure 5 is written once and serves whatever slot asks
		expect(captionFor(5, 'b')).toEqual(captionFor(5));
		expect(captionFor(999)).toBeNull();
	});

	it("renders the author's small mark-up and nothing else", () => {
		expect(renderCaption('credited [here](#sources).')).toBe(
			'credited <a href="#sources">here</a>.'
		);
		expect(renderCaption('*so* and **so**')).toBe('<em>so</em> and <strong>so</strong>');
		// raw HTML in the file can never reach the page as markup
		expect(renderCaption('<script>x</script> & co')).toBe(
			'&lt;script&gt;x&lt;/script&gt; &amp; co'
		);
	});
});
