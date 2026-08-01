<script lang="ts">
	interface Props {
		value: string;
		label: string;
		/** second line that qualifies or contradicts the number */
		compare?: string;
		/** value-basis note, e.g. "effective €" / "stated €" */
		basis?: string;
		color?: string;
	}
	let { value, label, compare = '', basis = '', color = 'var(--ink)' }: Props = $props();
</script>

<div class="stat">
	<div class="value" style:color>{value}</div>
	<div class="label">{label}</div>
	{#if compare}<div class="compare">{compare}</div>{/if}
	{#if basis}<div class="basis">{basis}</div>{/if}
</div>

<style>
	.stat {
		border-top: 3px solid var(--line-strong);
		padding-top: var(--sp-2);
	}
	.value {
		font-size: var(--fs-28);
		font-weight: 700;
		line-height: 1.1;
		letter-spacing: -0.01em;
	}
	.label {
		font-size: var(--fs-14);
		color: var(--ink-soft);
		margin-top: var(--sp-1);
	}
	.compare {
		font-size: var(--fs-13);
		color: var(--ink);
		margin-top: var(--sp-1);
	}
	.basis {
		font-size: var(--fs-12);
		color: var(--ink-faint);
		margin-top: var(--sp-1);
	}
</style>
