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
