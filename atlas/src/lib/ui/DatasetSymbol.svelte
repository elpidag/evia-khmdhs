<script lang="ts">
	/**
	 * A site symbol. Until the user's images arrive it is a square in the
	 * symbol's hue carrying text: `named` prints the artboards' «space for
	 * symbol» (the hub, where a caption underneath names the stream),
	 * `labelled` prints the stream's own name inside (the header band).
	 * `src` then replaces the text in this one file and every surface
	 * follows. `size` is a number of px or any CSS length.
	 *
	 * On the BLACK header band (Artboard 4, user 2026-08-27) the square is
	 * FILLED with the symbol's `chip` tone; the lettering takes black or
	 * white by that tone's luminance, and shrinks for a long name so it
	 * always fits the 59,5 px square.
	 */
	import { symbolFor, type SymbolKey } from '$lib/datasets';
	import { cssLuminance } from '$lib/theme.svelte';
	let {
		key,
		size = 96,
		named = false,
		labelled = false,
		band = false,
		active = false,
		src = null
	}: {
		key: SymbolKey;
		size?: number | string;
		named?: boolean;
		/** print the stream's name inside the square */
		labelled?: boolean;
		/** the header band's filled form */
		band?: boolean;
		active?: boolean;
		src?: string | null;
	} = $props();
	const s = $derived(symbolFor(key));
	const css = $derived(typeof size === 'number' ? `${size}px` : size);
	const text = $derived(s.short ?? s.label);
	/** white on a dark tone, black on a light one — the chip tones are CSS
	 *  strings over the tokens, so measure the resolved colour */
	const ink = $derived.by(() => (cssLuminance(s.chip) > 0.6 ? '#000' : '#fff'));
	/** 14 px for a short name, less for a long one, so it never overflows */
	const fs = $derived(
		`clamp(9px, calc(var(--sym-size) * ${(0.235 * Math.min(1, 17 / Math.max(17, text.length))).toFixed(3)}), 14px)`
	);
</script>

<span
	class="sym"
	class:active
	class:named
	class:band
	style:--sym-color={band ? s.chip : s.color}
	style:--sym-ink={ink}
	style:--sym-fs={fs}
	style:--sym-size={css}
	aria-hidden={named || labelled ? undefined : true}
>
	{#if src}
		<img {src} alt="" />
	{:else if labelled}
		<span class="ph name">{text}</span>
	{:else if named}
		<span class="ph">space for symbol</span>
	{/if}
</span>

<style>
	.sym {
		display: inline-flex;
		align-items: center;
		justify-content: center;
		box-sizing: border-box;
		width: var(--sym-size);
		height: var(--sym-size);
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
	/* the band's form: a solid tile of the tone, no border */
	.sym.band {
		background: var(--sym-color);
		border: none;
		color: var(--sym-ink);
	}
	/* the page you are on keeps a hairline ring, the only wayfinding the
	   band has left now that every square is filled */
	.sym.band.active {
		/* a black gap then a white ring, so the mark is visible whatever
		   the tone and whatever sits behind it */
		box-shadow:
			0 0 0 2px #000,
			0 0 0 4px #fff;
	}
	.sym img {
		display: block;
		width: 100%;
		height: 100%;
		object-fit: contain;
	}
	/* the artboards set the placeholder in Obviously Condensed Bold at
	   ~a fifth of the square (36 px in the hub's 186) */
	.ph {
		font-family: var(--font-display-cond);
		font-weight: 700;
		font-size: clamp(9px, calc(var(--sym-size) * 0.19), 36px);
		line-height: 1.1;
		text-align: center;
		padding: 4px;
		color: var(--ink-faint);
		overflow-wrap: anywhere;
	}
	.ph.name {
		font-size: var(--sym-fs);
		line-height: 1.12;
		padding: 3px;
		color: inherit;
	}
</style>
