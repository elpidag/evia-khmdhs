<script lang="ts">
	import { goto } from '$app/navigation';
	import { page } from '$app/state';

	let { placeholder = 'Search…' }: { placeholder?: string } = $props();

	let value = $state(page.url.searchParams.get('q') ?? '');
	let timer: ReturnType<typeof setTimeout> | undefined;

	function apply() {
		const url = new URL(page.url);
		if (value.trim()) url.searchParams.set('q', value.trim());
		else url.searchParams.delete('q');
		goto(url, { replaceState: true, keepFocus: true, noScroll: true });
	}
	function onInput() {
		clearTimeout(timer);
		timer = setTimeout(apply, 350);
	}
</script>

<input
	type="search"
	bind:value
	oninput={onInput}
	onkeydown={(e) => e.key === 'Enter' && apply()}
	{placeholder}
	aria-label="Search"
/>

<style>
	input {
		font: inherit;
		width: 100%;
		max-width: 34rem;
		padding: var(--sp-2) var(--sp-3);
		border: 1px solid var(--line-strong);
		border-radius: var(--radius);
		background: var(--paper);
		color: var(--ink);
	}
	input:focus {
		outline: 2px solid var(--accent);
		outline-offset: 1px;
	}
</style>
