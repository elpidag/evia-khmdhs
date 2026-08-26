<script lang="ts">
	/**
	 * A site symbol. Until the user's images arrive it is a bordered square
	 * in the symbol's hue carrying its label; `src` then replaces the text
	 * in this one file and every surface follows.
	 */
	import { symbolFor, type SymbolKey } from '$lib/datasets';
	let {
		key,
		size = 96,
		named = false,
		active = false,
		src = null
	}: { key: SymbolKey; size?: number; named?: boolean; active?: boolean; src?: string | null } =
		$props();
	const s = $derived(symbolFor(key));
</script>

<span
	class="sym"
	class:active
	class:named
	style:--sym-color={s.color}
	style:width="{size}px"
	style:height="{size}px"
	aria-hidden={named ? undefined : true}
>
	{#if src}
		<img {src} alt="" width={size} height={size} />
	{:else if named}
		<!-- the mock's placeholder wording until the image arrives; the
		     caption under the square carries the name -->
		<span class="ph">space for symbol</span>
	{/if}
</span>

<style>
	.sym {
		display: inline-flex;
		align-items: center;
		justify-content: center;
		box-sizing: border-box;
		border: 1.5px solid var(--sym-color);
		background: var(--paper);
		color: var(--sym-color);
		flex: none;
		overflow: hidden;
		transition: background 0.15s ease;
	}
	.sym.active {
		background: var(--sym-color);
		color: var(--paper);
	}
	.sym img {
		display: block;
		width: 100%;
		height: 100%;
		object-fit: contain;
	}
	.ph {
		font-family: var(--font-display);
		font-weight: 400;
		font-size: var(--fs-13);
		line-height: 1.15;
		text-align: center;
		padding: 6px;
		color: var(--ink-faint);
	}
</style>
