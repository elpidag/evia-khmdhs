<script lang="ts">
	/**
	 * A figure inside the written text, read from the page's payload instead of
	 * typed: `<Num id="antinero.contracts" />`. See `numbers.ts` for the rule.
	 */
	import { page } from '$app/state';
	import { dev } from '$app/environment';
	import { NUMBERS } from './numbers';

	let { id }: { id: string } = $props();

	const value = $derived.by(() => {
		const fn = NUMBERS[id];
		if (!fn) return null;
		try {
			return fn(page.data as Parameters<typeof fn>[0]);
		} catch {
			return null;
		}
	});
</script>

{#if value}{value}{:else}<span class="miss" title={dev ? `no value for «${id}»` : undefined}
		>{dev ? `«${id}?»` : '—'}</span
	>{/if}

<style>
	.miss {
		color: var(--c-flag-red);
	}
</style>
