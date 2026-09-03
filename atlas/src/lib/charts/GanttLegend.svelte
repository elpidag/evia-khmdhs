<script lang="ts">
	/**
	 * Legend for the sponsor-project Gantt, in two switchable variants:
	 * - "compact" (default): one wrapping line of chip+label entries, closed
	 *   by the shape-encoding note.
	 * - "panel": tinted colour key beside a "how to read a row" schematic.
	 * All lettering is var(--fs-14), matching the status-waffle legend; the
	 * schematic is HTML/CSS (percent-based bars, real text) so its type
	 * never scales with the page width. Entries only render when the data
	 * contains them; colours import from ganttTheme so chart and legend can
	 * never drift.
	 */
	import { COLOR, EXT_COLOR, NODATE_COLOR, noDate, type GanttProject } from './ganttTheme';

	interface Props {
		projects: GanttProject[];
		variant?: 'compact' | 'panel';
	}
	let { projects, variant = 'compact' }: Props = $props();

	const has = $derived({
		completed: projects.some((p) => p.status === 'completed'),
		active: projects.some((p) => p.status === 'active' && p.deadline),
		late: projects.some((p) => p.status === 'no_completion_recorded'),
		revoked: projects.some((p) => p.status === 'revoked'),
		nodate: projects.some(noDate)
	});
	/** a status colour as it actually renders where the extension segment
	 *  is drawn at 0.35 opacity over the white page */
	const pale = (c: string) => `color-mix(in srgb, ${c} 35%, white)`;

	const NOTE =
		'bar height is proportional to the announced budget, thick line = no budget announced, a step marks a restatement, paler shade = amendment (time extension / modification)';
</script>

{#if variant === 'panel'}
	<div class="legendbox">
		<div class="how" role="img" aria-label="How to read a row of the timeline">
			<div class="mrow">
				<span class="m start">designation act</span>
				<span class="m break">initial deadline</span>
				<span class="m end">current deadline</span>
				<i class="gv gstart"></i>
				<i class="gv gmid"></i>
				<i class="grule"></i>
			</div>
			<span class="dlab">no budget stated</span>
			<div class="track"><i class="b thin"></i><i class="g thin"></i></div>
			<div class="dnote">time extension</div>
			<span class="dlab">budgeted</span>
			<div class="track"><i class="b thick"></i><i class="g thick"></i></div>
			<div class="dnote">modification of aspects of the project</div>
		</div>

		<ul class="pkey">
			{#if has.completed}
				<li>
					<span class="sw"
						><i style:background={COLOR.completed}></i><i
							style:background={pale(COLOR.completed)}
						></i></span
					>
					projects with identified completion act
				</li>
			{/if}
			{#if has.active}
				<li>
					<span class="sw"
						><i style:background={COLOR.active}></i><i style:background={EXT_COLOR.active}
						></i></span
					>
					projects within deadline — no completion act identified
				</li>
			{/if}
			{#if has.nodate}
				<li>
					<span class="sw"><i style:background={NODATE_COLOR}></i></span>
					projects without specific dates for implementation
				</li>
			{/if}
			{#if has.late}
				<li>
					<span class="sw"
						><i style:background={COLOR.no_completion_recorded}></i><i
							style:background={pale(COLOR.no_completion_recorded)}
						></i></span
					>
					projects past deadline — no completion act identified
				</li>
			{/if}
		</ul>

		<ul class="mkey">
			{#if has.completed}
				<li><span class="mk ok">✔</span>date of act certifying completion</li>
			{/if}
			{#if has.revoked}
				<li><span class="mk bad">✖</span>revocation date</li>
			{/if}
		</ul>
	</div>
{:else}
	<ul class="key">
		{#if has.completed}
			<li>
				<span class="sw"
					><i style:background={COLOR.completed}></i><i style:background={pale(COLOR.completed)}
					></i></span
				>
				completion act identified
			</li>
		{/if}
		{#if has.active}
			<li>
				<span class="sw"
					><i style:background={COLOR.active}></i><i style:background={EXT_COLOR.active}></i></span
				>
				no completion act — still inside deadline
			</li>
		{/if}
		{#if has.nodate}
			<li>
				<span class="sw"><i style:background={NODATE_COLOR}></i></span>
				no implementation dates set
			</li>
		{/if}
		{#if has.late}
			<li>
				<span class="sw"
					><i style:background={COLOR.no_completion_recorded}></i><i
						style:background={pale(COLOR.no_completion_recorded)}
					></i></span
				>
				no completion act — deadline passed
			</li>
		{/if}
		{#if has.completed}
			<li><span class="mk ok">✔</span>completion date</li>
		{/if}
		{#if has.revoked}
			<li><span class="mk bad">✖</span>revocation date</li>
		{/if}
		<li class="note">{NOTE}</li>
	</ul>
{/if}

<style>
	/* ------- shared chips & marks (12px chips, like the waffle legend) ------- */
	.sw {
		display: inline-flex;
		flex: none;
	}
	.sw i {
		width: 12px;
		height: 12px;
		border-radius: 2px;
		display: inline-block;
	}
	.sw i:first-child:not(:only-child) {
		border-radius: 2px 0 0 2px;
	}
	.sw i + i {
		border-radius: 0 2px 2px 0;
	}
	.mk {
		font-weight: 900;
		font-size: var(--fs-14);
		width: 12px;
		flex: none;
		text-align: center;
		line-height: 1.2;
	}
	.mk.ok {
		color: var(--c-anadohoi);
	}
	.mk.bad {
		color: var(--ink);
	}
	.note {
		color: var(--ink-faint);
		font-style: italic;
	}

	/* ------- compact variant ------- */
	.key {
		list-style: none;
		margin: 0 0 var(--sp-3);
		padding: 0;
		display: flex;
		flex-wrap: wrap;
		gap: 4px var(--sp-4, 1rem);
		font-size: var(--fs-14);
		color: var(--ink-soft);
	}
	.key li {
		display: flex;
		align-items: center;
		gap: 8px;
	}

	/* ------- panel variant: tinted key beside a plain schematic ------- */
	/* one continuous tinted strip: schematic | colour key | ✓✕ marks */
	.legendbox {
		display: grid;
		grid-template-columns: auto minmax(0, 1fr) max-content;
		gap: var(--sp-1) var(--sp-5, 1.25rem);
		align-items: center;
		background: color-mix(in srgb, var(--ink) 5.8%, var(--paper));
		border-radius: 6px;
		padding: var(--sp-2) var(--sp-3);
		margin: 0 0 var(--sp-3);
	}
	.mkey {
		list-style: none;
		/* pulled in from the strip's right edge, per layout tuning */
		margin: 0 60px 0 0;
		padding: 0;
		display: flex;
		flex-direction: column;
		gap: var(--sp-2);
		font-size: var(--fs-14);
		color: var(--ink-soft);
	}
	.mkey li {
		display: flex;
		align-items: center;
		gap: 8px;
	}
	.pkey {
		list-style: none;
		/* nudged to the right, per layout tuning */
		margin: 0 0 0 28px;
		padding: 0;
		display: flex;
		flex-direction: column;
		gap: var(--sp-2);
		font-size: var(--fs-14);
		color: var(--ink-soft);
	}
	.pkey li {
		display: flex;
		align-items: flex-start;
		gap: 8px;
		line-height: 1.25;
	}
	.pkey .sw {
		margin-top: 2px;
		/* fixed swatch column (pair width) so single-chip entries' text
		   aligns with the pair entries' text */
		width: 24px;
	}

	/* the schematic: real text at the legend size over percent-based bars,
	   so lettering stays identical at every page width */
	.how {
		position: relative;
		display: grid;
		grid-template-columns: max-content 1fr;
		column-gap: 8px;
		row-gap: 3px;
		align-items: center;
		font-size: var(--fs-14);
		line-height: 1.15;
		width: 370px;
		max-width: 100%;
		/* nudged one chip-width (12px) to the right, per layout tuning */
		margin-left: 12px;
	}
	/* one-line milestone band, each label centred over its own vertical
	   guide: solid at the designation act, dashed at the initial deadline,
	   bold rule at the current deadline */
	.mrow {
		grid-column: 2;
		position: relative;
		height: 1.35em;
		color: var(--ink-soft);
	}
	.m {
		position: absolute;
		top: 0;
		white-space: nowrap;
	}
	.m.start {
		left: 0;
		transform: translateX(-50%);
	}
	.m.break {
		left: 45%;
		transform: translateX(-50%);
	}
	.m.end {
		right: 0;
		transform: translateX(18px);
	}
	.gv {
		position: absolute;
		top: 100%;
		width: 0;
		height: 41px;
		border-right: 1px dashed var(--line-strong);
	}
	.gv.gstart {
		left: 0;
	}
	.gv.gmid {
		left: 45%;
	}
	.grule {
		position: absolute;
		top: 100%;
		right: 0;
		width: 0;
		height: 57px;
		border-right: 2px solid var(--ink);
	}
	.dlab {
		grid-column: 1;
		justify-self: end;
		color: var(--ink);
	}
	.track {
		grid-column: 2;
		display: flex;
	}
	.track i {
		display: block;
	}
	.track .b {
		width: 45%;
	}
	.track .g {
		width: 55%;
	}
	.b {
		background: var(--ink);
	}
	.g {
		background: var(--line);
	}
	.thin {
		height: 3px;
	}
	.thick {
		height: 13px;
	}
	/* the annotations sit centred over the grey (post-deadline) zone */
	.dnote {
		grid-column: 2;
		width: 55%;
		margin-left: 45%;
		text-align: center;
		color: var(--ink);
	}
	@media (max-width: 900px) {
		.legendbox {
			grid-template-columns: 1fr;
		}
	}
</style>
