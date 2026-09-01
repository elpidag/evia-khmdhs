<script lang="ts">
	/**
	 * The story's right column — the author's Page01 artboard, FOLLOWING THE
	 * READER (their ruling, 2026-09-02): a square image slot showing the
	 * figure IN FORCE at the passage being read (it changes at the author's
	 * own `[FIGURE xx: name]` markers), the «Figure xx _ …» caption written
	 * under it, and under that ONLY the footnotes of the paragraphs currently
	 * on screen, in two columns behind a small «Footnote» label — never more
	 * than the screen's own notes, so nothing scrolls.
	 *
	 * The images themselves are still with the author; until they arrive the
	 * square names its figure.
	 */
	interface Props {
		figure: { n: number; name: string } | null;
		notes: { n: number; text: string }[];
	}
	let { figure, notes }: Props = $props();

	const pad = (n: number) => String(n).padStart(2, '0');
</script>

<div class="fig">
	<div class="box">
		{#if figure}
			{#key figure.n}
				<span class="ph">figure {pad(figure.n)} · {figure.name}</span>
			{/key}
		{/if}
	</div>
	<!-- the caption line the artboard writes under the image -->
	<p class="cap">{figure ? `Figure ${pad(figure.n)} _ ${figure.name}` : ''}</p>
	{#if notes.length}
		<div class="fnblock">
			<p class="fnlabel">Footnote</p>
			<ol class="notes">
				{#each notes as n (n.n)}
					<li value={n.n}>{n.text}</li>
				{/each}
			</ol>
		</div>
	{/if}
</div>

<style>
	.fig {
		display: grid;
		grid-template-rows: auto auto minmax(0, 1fr);
		row-gap: var(--sp-2); /* the caption sits close under the rectangle */
		width: 100%;
		height: 100%;
		/* caption and notes are set to the IMAGE's width, not the column's */
		--fig-w: min(100%, 540px);
	}
	.box {
		/* the artboard's square, inset in its column */
		width: var(--fig-w);
		aspect-ratio: 1;
		background: var(--paper-2);
		display: grid;
		place-items: center;
	}
	.cap {
		margin: 0;
		max-width: var(--fig-w);
		font-size: var(--fs-12);
		line-height: 1.35;
		color: var(--ink-soft);
		min-height: 1.35em;
	}
	/* the artboard's footnote block: a small «Footnote» label, then the notes
	   in TWO columns to the image's width, 12 px light. Only the visible
	   paragraphs' notes print, so the set stays short by construction. */
	.fnblock {
		max-width: var(--fig-w);
		min-height: 0;
		margin-top: var(--sp-3);
		overflow: hidden;
	}
	.fnlabel {
		margin: 0 0 var(--sp-2);
		font-size: var(--fs-12);
		line-height: 1.2;
		color: var(--ink-soft);
	}
	.notes {
		margin: 0;
		padding-left: 1.2em;
		columns: 2;
		column-gap: var(--sp-7);
		font-size: var(--fs-12);
		line-height: 1.3;
		font-weight: 300;
		color: var(--ink-soft);
	}
	.notes li {
		break-inside: avoid;
		margin-bottom: var(--sp-2);
	}
	.ph {
		font-size: var(--fs-12);
		color: var(--ink-faint);
	}

	@media (max-width: 1100px) {
		/* released: the rail becomes a plain block under the text */
		.fig {
			height: auto;
		}
	}
</style>
