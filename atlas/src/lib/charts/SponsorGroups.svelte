<script lang="ts">
	/**
	 * The sponsors gathered into the KIND of business each one is (user,
	 * DATA_DECISIONS 2026-08-25) — the finding the flat ranking beside it
	 * cannot show: half the committed money comes from electricity and
	 * banking.
	 *
	 * The form the user chose: one bar per group, clicking it opens the
	 * member companies underneath, member bars on the groups' own scale so
	 * a firm's bar is comparable with the group totals above it.
	 *
	 * TWO LENSES (user, 2026-08-25): «€ committed» carries the money;
	 * «number of projects» carries a count and nothing else, so one of the
	 * two is always the quick read. Each lens sorts by its own measure, as
	 * CONTRACT TYPE does.
	 *
	 * The DRESS is BarH's inside mode, deliberately (user, third round the
	 * same day: the first drawing wore heavier letters, shorter bars and
	 * its own stacked layout, and the pair's two halves read as different
	 * species): 35 px group bars with the name INSIDE in white fs-13 —
	 * wrapping to two lines exactly as BarH does — the value right after
	 * the bar in soft ink, no table rules, no uppercase. The per-row
	 * «· M without a stated sum» tail is what starved the bars of length,
	 * so under the € lens it survives only where the € say nothing (the
	 * «—» groups); the full counts are one toggle away, and the caveat
	 * carries the rule.
	 *
	 * Every width is measured from hidden copies (BarH's own technique) —
	 * a character-count constant was wrong at every other width.
	 */
	import { eurShort, grInt } from '$lib/transforms/format';

	export interface SponsorGroup {
		key: string;
		label: string;
		eur: number;
		n: number;
		unstated: number;
		members: {
			company: string;
			budget: number;
			n: number;
			unstated: number;
			basis: string;
		}[];
	}
	interface Props {
		groups: SponsorGroup[];
		/** the measure the bars carry: money, or a plain project count */
		lens?: 'eur' | 'n';
	}
	let { groups, lens = 'eur' }: Props = $props();

	let open = $state<string | null>(null);
	let boxW = $state(0);

	const val = (v: { eur: number; n: number }) => (lens === 'eur' ? v.eur : v.n);
	const mval = (m: { budget: number; n: number }) => (lens === 'eur' ? m.budget : m.n);
	/** each lens sorts by its own measure; ties fall back to the count then
	 *  the label, or the three €0 groups would shuffle between loads */
	const rows = $derived(
		[...groups]
			.map((g) => ({ ...g, members: [...g.members].sort((a, b) => mval(b) - mval(a)) }))
			.sort((a, b) => val(b) - val(a) || b.n - a.n || a.label.localeCompare(b.label))
	);
	const max = $derived(Math.max(1, ...rows.map(val)));
	const allMembers = $derived(rows.flatMap((g) => g.members));

	const projects = (n: number) => `${grInt(n)} project${n === 1 ? '' : 's'}`;
	/** the value after the bar — € under the money lens (an unstated-only
	 *  row prints «—»), the plain count under the other */
	const groupValue = (g: SponsorGroup) =>
		lens === 'eur' ? (g.eur ? eurShort(g.eur) : '—') : projects(g.n);
	const memberValue = (m: SponsorGroup['members'][number]) =>
		lens === 'eur' ? (m.budget ? eurShort(m.budget) : '—') : projects(m.n);
	/** the honesty note beside a bar-less «—»: what the row DOES hold */
	const dashNote = (c: { n: number; unstated: number }) =>
		lens === 'eur' && c.unstated && c.unstated === c.n
			? `${projects(c.n)} · no stated sum`
			: '';

	/* measured off-screen, BarH's technique: the names, their longest word
	   (a two-line wrap is only honest when both halves fit) and the widest
	   value — the bars stop before the value column, so its width must be
	   real, not guessed */
	let labW = $state<number[]>([]);
	let wordW = $state<number[]>([]);
	let memW = $state<number[]>([]);
	let valW = $state<number[]>([]);
	const longestWord = (s: string) =>
		s.split(' ').reduce((a, b) => (b.length > a.length ? b : a), '');
	const reserve = $derived(Math.max(56, ...valW.filter((v) => v > 0)) + 34);
	const plot = $derived(Math.max(60, boxW - reserve));
	const px = (v: number) => Math.max(0, (v / max) * plot);
	const w = (v: number) => `${px(v)}px`;
	/** BarH's tiers: 0 = name inside on one line · 1 = inside wrapped to
	 *  two (the 35 px group bars only) · 2 = after the bar, in ink */
	const tierOf = (v: number, i: number, twoLines: boolean) => {
		const bar = px(v);
		if ((labW[i] ?? Infinity) + 14 <= bar) return 0;
		if (
			twoLines &&
			(wordW[i] ?? Infinity) + 14 <= bar &&
			(labW[i] ?? Infinity) / 2 + 14 <= bar
		)
			return 1;
		return 2;
	};
	const mFits = (v: number, i: number) => (memW[i] ?? Infinity) + 14 <= px(v);
</script>

<div class="sg" bind:clientWidth={boxW}>
	<!-- hidden copies of every name and value, to measure the rendered
	     letters — the group spans wear the same uppercase as the rendered
	     ones, or the fit rules judge lowercase widths -->
	<div class="measure" aria-hidden="true">
		{#each rows as g, i (g.key)}
			<span class="glab" bind:clientWidth={labW[i]}>{g.label}</span>
			<span class="glab" bind:clientWidth={wordW[i]}>{longestWord(g.label)}</span>
			<span class="value" bind:clientWidth={valW[i]}>{groupValue(g)}</span>
		{/each}
		{#each allMembers as m, i (m.company)}
			<span bind:clientWidth={memW[i]}>{m.company}</span>
		{/each}
	</div>

	{#each rows as g, i (g.key)}
		{@const isOpen = open === g.key}
		{@const tier = tierOf(val(g), i, true)}
		<div class="grp">
			<button class="row" aria-expanded={isOpen} onclick={() => (open = isOpen ? null : g.key)}>
				<span class="bar" style:width={w(val(g))}>
					{#if tier < 2}
						<span class="on glab" class:two={tier === 1}>{g.label}</span>
					{/if}
				</span>
				{#if tier === 2}
					<span class="off glab">{g.label}</span>
				{/if}
				<!-- the value column at the row's right edge, table-style, on
				     both halves of the pair (user, 2026-08-25) -->
				<span class="tail">
					{#if dashNote(g)}<span class="note">{dashNote(g)}</span>{/if}
					<span class="value">{groupValue(g)}</span>
					<span class="caret" aria-hidden="true">{isOpen ? '▴' : '▾'}</span>
				</span>
			</button>

			{#if isOpen}
				<ul class="members">
					{#each g.members as m (m.company)}
						{@const mi = allMembers.indexOf(m)}
						{@const mOn = mFits(mval(m), mi)}
						<li title={m.basis}>
							<span class="mbar" style:width={w(mval(m))}>
								{#if mOn}<span class="mon">{m.company}</span>{/if}
							</span>
							{#if !mOn}<span class="off">{m.company}</span>{/if}
							<span class="tail">
								{#if dashNote(m)}<span class="note">{dashNote(m)}</span>{/if}
								<span class="value">{memberValue(m)}</span>
								<!-- the caret's width, so a member's value lines up
								     with its group's -->
								<span class="caret" aria-hidden="true"></span>
							</span>
						</li>
					{/each}
				</ul>
			{/if}
		</div>
	{/each}
</div>

<style>
	/* the whole dress is BarH's inside mode — same gaps, same faces, same
	   tiers — so the pair's two halves read as one chart family */
	.sg {
		display: grid;
		gap: var(--sp-2);
		position: relative;
	}
	.measure {
		position: absolute;
		visibility: hidden;
		height: 0;
		overflow: hidden;
		white-space: nowrap;
		/* must match the rendered letters the fit rules judge */
		font-size: var(--fs-13);
	}
	.measure span {
		display: inline-block;
	}
	.row {
		display: flex;
		align-items: center;
		gap: 6px;
		width: 100%;
		border: 0;
		background: none;
		font: inherit;
		text-align: left;
		cursor: pointer;
		padding: 0;
		color: var(--ink);
	}
	.bar {
		display: flex;
		align-items: center;
		flex: none;
		height: 35px;
		background: var(--c-anadohoi);
		border-radius: 2px;
	}
	.on {
		color: var(--paper);
		font-size: var(--fs-13);
		padding: 0 6px;
		white-space: nowrap;
		overflow: hidden;
	}
	/* two lines and no more — BarH's own clamp */
	.on.two {
		white-space: normal;
		line-height: 1.08;
		display: -webkit-box;
		-webkit-line-clamp: 2;
		line-clamp: 2;
		-webkit-box-orient: vertical;
		overflow: hidden;
	}
	.off {
		font-size: var(--fs-13);
		min-width: 0;
		line-height: 1.2;
	}
	/* the group names in caps (user, 2026-08-25) — same fs-13, no added
	   weight, so only the case tells a group from a company */
	.glab {
		text-transform: uppercase;
	}
	/* the whole value column at the row's right edge */
	.tail {
		margin-left: auto;
		display: flex;
		align-items: baseline;
		gap: var(--sp-2);
		flex: none;
	}
	.value {
		font-size: var(--fs-13);
		color: var(--ink-soft);
		white-space: nowrap;
		flex: none;
		font-variant-numeric: tabular-nums;
	}
	/* what a bar-less «—» row does hold */
	.note {
		font-size: var(--fs-12);
		color: var(--ink-faint);
		white-space: nowrap;
	}
	.caret {
		color: var(--ink-faint);
		width: 1em;
		text-align: center;
		flex: none;
	}
	/* the members, in a lighter tone of the same hue */
	.members {
		list-style: none;
		display: grid;
		gap: var(--sp-1);
		margin: var(--sp-1) 0 var(--sp-2);
		padding: 0 0 0 var(--sp-4);
	}
	.members li {
		display: flex;
		align-items: center;
		gap: 6px;
	}
	.mbar {
		display: flex;
		align-items: center;
		flex: none;
		height: 26px;
		background: color-mix(in srgb, var(--c-anadohoi) 32%, var(--paper));
		border-radius: 2px;
	}
	/* the member bars are pale, so a name on one stays ink */
	.mon {
		color: var(--ink);
		font-size: var(--fs-13);
		padding: 0 6px;
		white-space: nowrap;
		overflow: hidden;
	}
</style>
