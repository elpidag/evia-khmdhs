<script lang="ts">
	import type { Snippet } from 'svelte';

	/**
	 * Mounts its children only when scrolled near the viewport — below-fold
	 * charts cost nothing at navigation time. SSR and pre-scroll render a
	 * fixed-height skeleton so the page doesn't jump.
	 */
	interface Props {
		height?: number;
		children: Snippet;
	}
	let { height = 420, children }: Props = $props();

	let el = $state<HTMLElement | null>(null);
	let show = $state(false);

	$effect(() => {
		if (!el || show) return;
		const io = new IntersectionObserver(
			(entries) => {
				if (entries.some((e) => e.isIntersecting)) {
					show = true;
					io.disconnect();
				}
			},
			{ rootMargin: '500px 0px' }
		);
		io.observe(el);
		return () => io.disconnect();
	});
</script>

{#if show}
	{@render children()}
{:else}
	<div bind:this={el} class="skeleton" style:height={`${height}px`}></div>
{/if}
