/**
 * THE STORY'S TIMELINE EVENTS — the author's own `Timeline.xlsx`
 * (13_MARA/INVESTIGATIVE-REPORT), transcribed mechanically by
 * `scripts/import_story_timeline.py` on 2026-09-01, never by hand.
 * Re-run that script after the author edits the workbook.
 *
 * The spreadsheet's columns map straight onto the fields below —
 * CATEGORY → `lane`, START/END DATE → `date`/`end`, KEY TITLE → `title`,
 * EXPLANATION TEXT → `body`. Two things happen to the sheet on the way in,
 * both mechanical, both recorded here so a re-import reproduces them:
 *
 *  1. the CATEGORY column is written FOUR ways across the rows («Global
 *     events& EU Legislation changes» and «… & EU Legislative changes» are one
 *     lane); Sheet2 lists the three canonical names and the importer folds
 *     onto them.
 *  2. `id` is a short slug of the title. It is the anchor a bullet and its
 *     passage will be bound by, so it must stay stable; nothing else derives
 *     from it.
 *
 * `beat` is the one binding the spreadsheet does NOT carry: which passage of
 * the narrative mentions the event. Until the author's text is placed it is
 * unset on every row and the timeline follows the reader's progress instead.
 * Filling it in is what lets a bullet click through to its paragraph — and a
 * paragraph light its bullets.
 */
import type { Lane } from '$lib/transforms/storyTimeline';

export interface StoryEvent {
	/** stable slug of the title — the anchor a passage binds to */
	id: string;
	lane: Lane;
	/** ISO; every row of this sheet carries a full date */
	date: string;
	/** set only where the sheet gives a LATER end date: the event is a period */
	end?: string;
	title: string;
	/** the sheet's EXPLANATION TEXT; 12 of the 31 rows carry none */
	body?: string;
	/** the passage that mentions it — see above; none are bound yet */
	beat?: string;
}

export const EVENTS: StoryEvent[] = [
	{
		id: 'fires-in-the-peloponnese',
		lane: 'fire',
		date: '2007-08-24',
		end: '2007-08-27',
		title: 'Fires in the Peloponnese'
	},
	{
		id: 'law-3889-2010-formalised',
		lane: 'greece',
		date: '2010-10-14',
		title: 'Law 3889/2010 formalised the framework for external preparation of Forest Maps (FEK 182A)',
		body: 'Article 13 allowed the technical preparation of Forest Maps to be assigned externally when Forest Service departments could not undertake it themselves.'
	},
	{
		id: 'law-4423-2016-redefined',
		lane: 'greece',
		date: '2016-09-27',
		title: 'Law 4423/2016 redefined the legal framework for forest cooperatives',
		body: 'While recognising cooperatives as organised actors in forest management and exploitation, the law also introduced clearer rules on membership and operation, alongside new electronic registries and a more formalised system of state registration and supervision.It also consolidated a firmer distinction between Forest Workers\' Cooperatives and Compulsory Forest Cooperatives. No new Compulsory Forest Cooperatives could be established, while the existing ones remained responsible for the management and exploitation of forests jointly owned by their members.'
	},
	{
		id: 'fires-in-mati-attica',
		lane: 'fire',
		date: '2018-07-23',
		title: 'Fires in Mati, Attica'
	},
	{
		id: 'european-electronic-communications-code-directive',
		lane: 'world',
		date: '2018-12-11',
		title: 'European Electronic Communications Code — Directive (EU) 2018/1972',
		body: 'Article 110 required EU Member States to establish public warning systems capable of transmitting alerts concerning imminent or developing major emergencies and disasters to affected mobile users by 21 June 2022.'
	},
	{
		id: 'launch-of-the-interim-outbound',
		lane: 'greece',
		date: '2019-08-10',
		title: 'Launch of the interim outbound 112 warning system',
		body: 'An interim version of the outbound 112 service entered operation, allowing Civil Protection to send geographically targeted emergency warnings through SMS and Cell Broadcast.'
	},
	{
		id: 'european-green-deal',
		lane: 'world',
		date: '2019-12-11',
		title: 'European Green Deal',
		body: 'The European Commission presented the European Green Deal, establishing its strategy for climate neutrality and the green transition.'
	},
	{
		id: 'full-operational-launch',
		lane: 'greece',
		date: '2020-01-11',
		title: 'Full operational launch of the 112 Emergency Communications Service',
		body: 'The fully developed 112 service entered operational use, integrating its inbound emergency-call function with an outbound system for geographically targeted public warnings.'
	},
	{
		id: 'eu-forest-strategy-for-2030',
		lane: 'world',
		date: '2021-07-16',
		title: 'EU Forest Strategy for 2030',
		body: 'The European Commission adopted the EU Forest Strategy for 2030, linking forest protection and restoration to the European Green Deal, biodiversity objectives and climate neutrality.'
	},
	{
		id: 'european-climate-law-entered-into',
		lane: 'world',
		date: '2021-07-29',
		title: 'European Climate Law entered into force',
		body: 'Regulation (EU) 2021/1119 made the EU’s 2050 climate-neutrality objective legally binding and established a net greenhouse-gas emissions-reduction target of at least 55% by 2030.'
	},
	{
		id: 'extensive-use-of-112-emergency',
		lane: 'greece',
		date: '2021-08-03',
		end: '2021-08-16',
		title: 'Extensive use of 112 emergency alerts during the 2021 fire season',
		body: '112 emergency alerts were deployed extensively to issue instructions for evacuation of settlements in proximity of ongoing fires.'
	},
	{
		id: 'fires-in-the-peloponese',
		lane: 'fire',
		date: '2021-08-03',
		end: '2021-08-12',
		title: 'Fires in the Peloponese'
	},
	{
		id: 'fires-in-northern-attica',
		lane: 'fire',
		date: '2021-08-03',
		end: '2021-08-07',
		title: 'Fires in northern Attica'
	},
	{
		id: 'fires-in-northern-evia',
		lane: 'fire',
		date: '2021-08-03',
		end: '2021-08-11',
		title: 'Fires in northern Evia'
	},
	{
		id: 'prime-minister-s-press-conference',
		lane: 'greece',
		date: '2021-08-12',
		title: 'Prime Minister\'s press conference',
		body: 'Announcement of the North Evia reconstruction programme and the restoration and reforestation contractor mechanism.'
	},
	{
		id: 'emergency-legislative-act-on-fire',
		lane: 'greece',
		date: '2021-08-13',
		title: 'Emergency legislative act on fire response and post-fire restoration (FEK 143A)',
		body: 'The act transferred the Forest Services from the Decentralised Administrations to the Ministry of Environment and Energy, introduced the arogi.gov.gr platform for state relief, established the restoration and reforestation contractor mechanism, and introduced additional wildfire-relief measures.'
	},
	{
		id: 'fires-in-western-attica',
		lane: 'fire',
		date: '2021-08-16',
		title: 'Fires in western Attica'
	},
	{
		id: 'law-4824-2021-ratified',
		lane: 'greece',
		date: '2021-09-02',
		title: 'Law 4824/2021 ratified the 13 August emergency act, making the restoration and reforestation contractor a permanent part of forest legislation'
	},
	{
		id: 'law-4843-2021-introduces-special',
		lane: 'greece',
		date: '2021-10-20',
		title: 'Law 4843/2021 introduces special procurement for urgent post-fire works',
		body: 'Article 74 introduced accelerated procurement for urgent erosion- and flood-control works in areas affected by extensive fires or floods that had been declared under a state of emergency. It allowed direct award below EU thresholds or negotiation without prior publication, with the awarding procedure to be completed within ten days from the call.'
	},
	{
		id: 'law-4876-2021-extends-exceptional',
		lane: 'greece',
		date: '2021-12-23',
		title: 'Law 4876/2021 extends exceptional procurement to broader forestry works',
		body: 'Article 76 extended the special procedures beyond emergency recovery to studies, support services, forest clearing, forest roads and firebreaks, and removed the ordinary annual aggregate limit. For the covered works, the ordinary €60,000 direct-award ceiling was replaced by the applicable EU threshold.'
	},
	{
		id: 'greek-national-climate-law',
		lane: 'greece',
		date: '2022-05-27',
		title: 'Greek National Climate Law',
		body: 'Law 4936/2022 established Greece’s national climate-neutrality framework, under which certain corporate emissions-reduction obligations may partly be met through planting, afforestation and reforestation, linking forests more directly to emerging carbon-accounting infrastructures.'
	},
	{
		id: 'official-launch-of-the-antinero',
		lane: 'greece',
		date: '2022-07-08',
		title: 'Official launch of the Anti-nero programme by the Ministry of Environment and Energy',
		body: '(see here)'
	},
	{
		id: 'initial-ratification-of-forest-maps',
		lane: 'greece',
		date: '2022-12-27',
		title: 'Initial Ratification of Forest Maps reached 90% of Greece',
		body: 'The Ministry of Environment and Energy announced that Forest Maps had been posted for 95% of the territory and initially ratified for 90%.'
	},
	{
		id: 'a-subcommittee-of-the-government',
		lane: 'greece',
		date: '2023-01-16',
		title: 'A subcommittee of the Government Committee for State Aid was established to monitor and coordinate implementation of the North Evia Reconstruction Programme'
	},
	{
		id: 'fires-in-rhodes',
		lane: 'fire',
		date: '2023-07-18',
		end: '2023-07-28',
		title: 'Fires in Rhodes'
	},
	{
		id: 'fires-in-evros',
		lane: 'fire',
		date: '2023-08-19',
		end: '2023-09-04',
		title: 'Fires in Evros'
	},
	{
		id: 'establishment-of-a-special-committee',
		lane: 'greece',
		date: '2023-11-21',
		title: 'Establishment of a Special Committee for the preparation of a Special Development Programme for Evros (FEK 6595D)'
	},
	{
		id: 'law-5106-introduced-the-hybrid',
		lane: 'greece',
		date: '2024-05-01',
		title: 'Law 5106 introduced the Hybrid Co-operative Schemes for the management of public forests (FEK 63A)'
	},
	{
		id: 'adoption-of-the-eu-carbon',
		lane: 'world',
		date: '2024-11-27',
		title: 'Adoption of the EU Carbon Removal Certification Framework adopted',
		body: 'Regulation (EU) 2024/3012 established a voluntary EU framework for certifying permanent carbon removals, carbon farming and carbon storage.'
	},
	{
		id: 'law-5281-2026-reformed-wildfire',
		lane: 'greece',
		date: '2026-02-25',
		title: 'Law 5281/2026 reformed wildfire prevention, preparedness and response',
		body: 'The law reorganised the wildfire and civil-protection framework, providing for a ten-year wildfire strategy, revised coordination structures, prescribed burning, controlled grazing, annual and post-incident evaluations, stronger arson investigation and reforms to firefighter training.'
	},
	{
		id: 'tender-for-forest-carbon-units',
		lane: 'greece',
		date: '2026-03-26',
		title: 'Tender for Forest Carbon Units and the Greek Voluntary Carbon Market',
		body: 'The Natural Environment & Climate Change Agency (N.E.C.C.A.) published a public tender for services to develop the framework for using carbon units generated from Greece’s forests and forest lands through the Greek Voluntary Carbon Market. The tender concerns the methodologies and tools needed to make forest carbon measurable, certifiable and potentially tradable within that system.'
	},
];

/** the events of one lane, in date order */
export function laneEvents(lane: Lane): StoryEvent[] {
	return EVENTS.filter((e) => e.lane === lane);
}

/** true where the sheet gave an end date: the event ran for a period */
export function isPeriod(e: StoryEvent): boolean {
	return !!e.end && e.end !== e.date;
}
