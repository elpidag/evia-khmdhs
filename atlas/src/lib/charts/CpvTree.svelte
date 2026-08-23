<script lang="ts">
	/**
	 * The declared CPV codes rolled up the vocabulary's own tree (user,
	 * 2026-08-23): one bar per DIVISION — contracts declaring at least one
	 * code under it — which opens into its classes, each opening into its
	 * codes. Names are the EU CPV 2008 vocabulary's (EN, Greek beneath),
	 * counts are distinct contracts and OVERLAP across rows (a contract
	 * declares ~16 codes), so nothing here is summed or drawn as a share.
	 */
	import { grInt } from '$lib/transforms/format';

	interface Code {
		code: string;
		name_en: string;
		name_el: string;
		n: number;
	}
	interface Cls extends Code {
		codes: Code[];
	}
	interface Division extends Code {
		classes: Cls[];
	}
	interface Props {
		divisions: Division[];
		/** the denominator of the bars — every in-scope contract */
		total: number;
		/** render the classes of ONE division directly, without its own row —
		 *  the columns chart above already is that row (2026-08-23) */
		classesOnly?: boolean;
	}
	let { divisions, total, classesOnly = false }: Props = $props();

	let open = $state<Record<string, boolean>>({});
	let openCls = $state<Record<string, boolean>>({});
	const toggle = (k: string) => (open[k] = !open[k]);
	const toggleCls = (k: string) => (openCls[k] = !openCls[k]);
	const pctOf = (n: number) => (total ? (n / total) * 100 : 0);
	/** «77» from «77000000-0» — the division's own number */
	const short = (code: string, len: number) => code.slice(0, len);
</script>

<div class="tree">
	{#each divisions as d (d.code)}
		<div class="div" class:open={open[d.code] || classesOnly}>
			{#if !classesOnly}
			<button class="row" onclick={() => toggle(d.code)} aria-expanded={!!open[d.code]}>
				<span class="caret" aria-hidden="true">{open[d.code] ? '−' : '+'}</span>
				<span class="name"
					><span class="code">{short(d.code, 2)}</span>{d.name_en}<small>{d.name_el}</small></span
				>
				<span class="barcell"><span class="bar" style:width={`${pctOf(d.n)}%`}></span></span>
				<span class="n">{grInt(d.n)}</span>
			</button>
			{/if}
			{#if open[d.code] || classesOnly}
				<div class="classes" class:bare={classesOnly}>
					{#each d.classes as k (k.code)}
						{@const kk = `${d.code}|${k.code}`}
						<div class="cls" class:open={openCls[kk]}>
							<button class="row sub" onclick={() => toggleCls(kk)} aria-expanded={!!openCls[kk]}>
								<span class="caret" aria-hidden="true">{openCls[kk] ? '−' : '+'}</span>
								<span class="name"
									><span class="code">{short(k.code, 4)}</span>{k.name_en}<small>{k.name_el}</small></span
								>
								<span class="barcell"><span class="bar thin" style:width={`${pctOf(k.n)}%`}></span></span>
								<span class="n">{grInt(k.n)}</span>
							</button>
							{#if openCls[kk]}
								<ul class="codes">
									{#each k.codes as c (c.code)}
										<li>
											<span class="code">{c.code}</span>
											<span class="cname">{c.name_en}<small>{c.name_el}</small></span>
											<span class="n">{grInt(c.n)}</span>
										</li>
									{/each}
								</ul>
							{/if}
						</div>
					{/each}
				</div>
			{/if}
		</div>
	{/each}
</div>

<style>
	.tree {
		display: grid;
		gap: 4px;
	}
	.row {
		display: grid;
		grid-template-columns: 1.2rem minmax(16rem, 34%) 1fr 3.5rem;
		align-items: center;
		gap: var(--sp-3);
		width: 100%;
		padding: 4px 0;
		border: 0;
		background: none;
		font: inherit;
		text-align: left;
		cursor: pointer;
		color: var(--ink);
	}
	.row:hover .name {
		text-decoration: underline;
	}
	.row.sub {
		padding-left: 1.2rem;
	}
	.caret {
		color: var(--ink-faint);
		font-size: var(--fs-14);
		text-align: center;
	}
	.name {
		font-size: var(--fs-13);
		line-height: 1.25;
	}
	.name small,
	.cname small {
		display: block;
		color: var(--ink-faint);
		font-size: var(--fs-12);
	}
	.code {
		display: inline-block;
		min-width: 2.6rem;
		margin-right: 0.4rem;
		color: var(--ink-faint);
		font-variant-numeric: tabular-nums;
		font-size: var(--fs-12);
	}
	.barcell {
		height: 28px;
		background: var(--paper-3, #f2f2f2);
		position: relative;
	}
	.bar {
		position: absolute;
		left: 0;
		top: 0;
		bottom: 0;
		background: var(--c-antinero);
	}
	.bar.thin {
		top: 8px;
		bottom: 8px;
		background: var(--ink-soft);
	}
	.n {
		text-align: right;
		font-weight: 700;
		font-variant-numeric: tabular-nums;
		font-size: var(--fs-13);
	}
	.classes {
		margin: 2px 0 8px;
		border-left: 2px solid var(--line);
		padding-left: var(--sp-2);
	}
	.classes.bare {
		margin: 0;
		border-left: 0;
		padding-left: 0;
	}
	.classes.bare .row.sub {
		padding-left: 0;
	}
	.codes {
		list-style: none;
		margin: 0 0 6px 2.4rem;
		padding: 0 0 0 var(--sp-3);
		border-left: 1px solid var(--line);
		display: grid;
		gap: 2px;
	}
	.codes li {
		display: grid;
		grid-template-columns: 6.5rem 1fr 3.5rem;
		gap: var(--sp-3);
		align-items: baseline;
		font-size: var(--fs-13);
	}
	.codes .code {
		min-width: 0;
		margin: 0;
	}
	.cname {
		color: var(--ink-soft);
	}
</style>
