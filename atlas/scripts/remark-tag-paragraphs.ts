// A paragraph that BEGINS with an inline tag — the author's `<span
// class="figmark">[FIGURE 04: …]</span> The 2021 fire season…` markers, a
// passage opening with a `<Num …/>` token — is emitted by mdsvex as a raw
// HTML block with no <p> around it (found 2026-09-02: /story warned «71
// rendered blocks vs 80 parsed», and the reading line could never reach the
// Figure 04 paragraph). Markdown proper treats an inline tag followed by
// text as a paragraph; this remark plugin restores that: a root-level `html`
// node that is not a lone tag and not real block-level HTML becomes a
// paragraph whose one child is that raw HTML — `<p><span …>…</span> The
// 2021 …</p>` — so `.prose > p` pairs 1:1 with the parsed blocks again.
// Text inside such a paragraph is raw, not markdown (no links or emphasis
// there — the author's files carry none; mdsvexParagraphs.test.ts guards).
const BLOCK =
	/^<\/?(p|div|h[1-6]|ul|ol|li|hr|table|thead|tbody|tr|td|th|blockquote|pre|section|article|aside|header|footer|figure|nav|script|style|details|summary)\b/i;
const LONE_TAG = /^<\/?[a-zA-Z][^<>]*\/?>$/;

/** the slice of mdast this plugin touches */
interface Node {
	type: string;
	value?: string;
	/** a shortcut reference's own text, brackets excluded */
	label?: string;
	position?: unknown;
	children?: Node[];
}

export function tagParagraphs() {
	return (tree: Node) => {
		tree.children = (tree.children ?? []).map((n): Node => {
			if (n.type !== 'html' || typeof n.value !== 'string') return n;
			const v = n.value.trim();
			if (BLOCK.test(v) || LONE_TAG.test(v)) return n;
			return { type: 'paragraph', children: [{ type: 'html', value: n.value }], position: n.position };
		});
	};
}

// The author writes their figure markers as PLAIN TEXT — `[FIGURE 05: Press
// conference]` — since 2026-09-03: the `<span class="figmark">…</span>`
// wrapper they used to have to type is markup in the middle of their prose,
// and it made the text hard to edit without breaking the page. This plugin
// puts the wrapper back at build time, so the marker still hides in the
// narrative and still marks where the figure changes.
//
// The trap: `[FIGURE 05: …]` is markdown's own shortcut-reference syntax, so
// remark hands it over as a `linkReference` node carrying the text in
// `label` — NOT as text with brackets. Both shapes are handled (a marker
// already inside a span is an `html` node and is left alone), and the
// paragraph around it stays a paragraph, so its prose is still markdown.
const MARKER = /\[FIGURE\s*\d+\s*(?::[^\]]*)?\]/g;
const LABEL = /^FIGURE\s*\d+\s*(?::.*)?$/i;

const span = (inner: string): Node => ({
	type: 'html',
	value: `<span class="figmark">${inner}</span>`
});

// The author's `[CHART: name]` on a line of its own (2026-09-04, KEY
// FINDINGS): the paragraph becomes a block-level placeholder
// `<div class="chartmark" data-chart="name"></div>` the story page mounts
// the chart into, full-bleed; tagParagraphs leaves a <div> alone, and
// content.ts skips the line, so the rendered <p>s still pair 1:1 with the
// parsed blocks.
const CHART = /^CHART:\s*([a-z0-9-]+)\s*$/i;

export function chartMarkers() {
	return (tree: Node) => {
		tree.children = (tree.children ?? []).map((n): Node => {
			if (n.type !== 'paragraph' || !n.children || n.children.length !== 1) return n;
			const only = n.children[0];
			const label =
				only.type === 'linkReference' && typeof only.label === 'string'
					? only.label
					: only.type === 'text' && typeof only.value === 'string'
						? only.value.trim().replace(/^\[|\]$/g, '')
						: null;
			const m = label ? CHART.exec(label.trim()) : null;
			if (!m) return n;
			return {
				type: 'html',
				value: `<div class="chartmark" data-chart="${m[1].toLowerCase()}"></div>`,
				position: n.position
			};
		});
	};
}

export function figureMarkers() {
	const walk = (n: Node): void => {
		if (!n.children) return;
		const out: Node[] = [];
		for (const child of n.children) {
			// `[FIGURE 05: …]` as markdown read it: a shortcut reference
			if (child.type === 'linkReference' && typeof child.label === 'string' && LABEL.test(child.label.trim())) {
				// a marker the author already wrapped by hand arrives as
				// `<span …>` · reference · `</span>`: give the text back as it
				// was rather than wrapping it twice
				const prev = out[out.length - 1];
				const wrapped =
					prev?.type === 'html' && /class="figmark">\s*$/.test(prev.value ?? '');
				out.push(wrapped ? { type: 'text', value: `[${child.label}]` } : span(`[${child.label}]`));
				continue;
			}
			// the same marker as literal text (inside another construct)
			if (child.type === 'text' && typeof child.value === 'string' && child.value.includes('[FIGURE')) {
				let last = 0;
				for (const m of child.value.matchAll(MARKER)) {
					const at = m.index ?? 0;
					if (at > last) out.push({ type: 'text', value: child.value.slice(last, at) });
					out.push(span(m[0]));
					last = at + m[0].length;
				}
				if (last < child.value.length) out.push({ type: 'text', value: child.value.slice(last) });
				continue;
			}
			walk(child);
			out.push(child);
		}
		n.children = out;
	};
	return (tree: Node) => walk(tree);
}
