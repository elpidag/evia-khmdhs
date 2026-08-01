<script lang="ts">
	import { page } from '$app/state';
	import { goto } from '$app/navigation';

	interface Props {
		param: string;
		options: { value: string; label: string }[];
		fallback: string;
	}
	let { param, options, fallback }: Props = $props();

	const current = $derived(page.url.searchParams.get(param) ?? fallback);

	function pick(value: string) {
		const url = new URL(page.url);
		if (value === fallback) url.searchParams.delete(param);
		else url.searchParams.set(param, value);
		goto(url, { replaceState: true, keepFocus: true, noScroll: true });
	}
</script>

<div class="toggle" role="group">
	{#each options as o (o.value)}
		<button class:active={current === o.value} onclick={() => pick(o.value)}>
			{o.label}
		</button>
	{/each}
</div>

<style>
	.toggle {
		display: inline-flex;
		border: 1px solid var(--line-strong);
		border-radius: var(--radius);
		overflow: hidden;
	}
	button {
		font: inherit;
		font-size: var(--fs-13);
		padding: var(--sp-1) var(--sp-3);
		border: 0;
		background: var(--paper);
		color: var(--ink-soft);
		cursor: pointer;
	}
	button + button {
		border-left: 1px solid var(--line);
	}
	button.active {
		background: var(--ink);
		color: var(--paper);
	}
</style>
