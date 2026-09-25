/**
 * The brand's two lines share their edges (the author, 2026-09-25): the C
 * of COVERED WITH MONEY starts under the S of SCORCHED and the Y ends under
 * the S of FORESTS, wherever the brand appears — the header, the landing's
 * title, the landing menu's title and the hub. A Svelte action on the
 * element that holds the `.l1` / `.l2` spans: it measures the first line's
 * glyph run (less the spacing CSS adds after its last letter), the second
 * line's natural run, and sets the second line's letter-spacing so that
 * its last glyph lands on the first line's right edge. Re-fitted when the
 * fonts arrive, when the element resizes (the sizes are vw-based) and on a
 * Theme Lab change (another face, another width).
 */
export function fitBrand(node: HTMLElement): { destroy(): void } {
	const l1 = node.querySelector<HTMLElement>('.l1');
	const l2 = node.querySelector<HTMLElement>('.l2');
	if (!l1 || !l2) return { destroy() {} };

	const run = (el: HTMLElement): number => {
		const r = document.createRange();
		r.selectNodeContents(el);
		return r.getBoundingClientRect().width;
	};

	const fit = () => {
		const text = l2.textContent ?? '';
		const n = text.length;
		if (n < 2) return;
		l2.style.letterSpacing = '0px';
		const trail1 = parseFloat(getComputedStyle(l1).letterSpacing) || 0;
		const w1 = run(l1) - trail1; // the box carries a spacing after the S too
		const w2 = run(l2);
		if (!(w1 > 0) || !(w2 > 0)) return;
		l2.style.letterSpacing = `${(w1 - w2) / (n - 1)}px`;
	};

	fit();
	const ro = typeof ResizeObserver !== 'undefined' ? new ResizeObserver(() => fit()) : null;
	ro?.observe(node);
	const onLab = () => fit();
	window.addEventListener('themelab:change', onLab);
	let alive = true;
	document.fonts?.ready.then(() => alive && fit());

	return {
		destroy() {
			alive = false;
			ro?.disconnect();
			window.removeEventListener('themelab:change', onLab);
		}
	};
}
