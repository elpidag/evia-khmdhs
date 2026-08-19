<script lang="ts">
	/**
	 * A section title with an arrow that opens it (user, 2026-08-19).
	 *
	 * Native <details>/<summary>, so it works without JS and keeps keyboard
	 * and screen-reader semantics; the h2 keeps the detail-template lettering
	 * (display face, 900, uppercase, fs-18) so a folded section reads exactly
	 * like an unfolded one.
	 */
	import type { Snippet } from 'svelte';

	interface Props {
		title: string;
		/** open on arrival — the page's spine sections do, the reference
		 *  blocks (quotes, CPV) wait to be asked for */
		open?: boolean;
		/** optional line printed under the title, inside the fold */
		children: Snippet;
	}
	let { title, open = false, children }: Props = $props();
</script>

<details class="fold" {open}>
	<summary>
		<span class="arrow" aria-hidden="true"></span>
		<h2>{title}</h2>
	</summary>
	<div class="body">{@render children()}</div>
</details>

<style>
	.fold {
		margin-top: var(--sp-8);
	}
	summary {
		display: flex;
		align-items: center;
		gap: 8px;
		cursor: pointer;
		list-style: none;
	}
	summary::-webkit-details-marker {
		display: none;
	}
	h2 {
		font-family: var(--font-display);
		font-weight: 900;
		text-transform: uppercase;
		font-size: var(--fs-18);
		letter-spacing: 0.01em;
		margin: 0;
	}
	.arrow {
		width: 0;
		height: 0;
		border-left: 7px solid var(--ink);
		border-top: 5px solid transparent;
		border-bottom: 5px solid transparent;
		transition: transform 0.12s ease;
	}
	.fold[open] .arrow {
		transform: rotate(90deg);
	}
	summary:hover h2 {
		color: var(--c-antinero);
	}
	.body {
		margin-top: var(--sp-3);
	}
</style>
