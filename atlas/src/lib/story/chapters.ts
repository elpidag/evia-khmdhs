/**
 * The story's chapters (user, 2026-08-27): a scroll the author writes over
 * the coming days. The ids are the anchors and the content file names
 * (src/content/story/<id>.md); the titles are placeholders to rename here.
 * KEY FINDINGS is the one chapter with substance today — the frames of
 * the former /compare page live in it.
 */
export interface Chapter {
	id: string;
	title: string;
}

export const CHAPTERS: Chapter[] = [
	{ id: 'intro', title: 'START HERE' },
	{ id: 'findings', title: 'KEY FINDINGS' },
	{ id: 'fire', title: 'THE FIRES' },
	{ id: 'money', title: 'THE MONEY' },
	{ id: 'awarding', title: 'AWARDING' },
	{ id: 'companies', title: 'THE COMPANIES' },
	{ id: 'coops', title: 'THE CO-OPERATIVES' },
	{ id: 'sponsors', title: 'THE SPONSORS' },
	{ id: 'supervision', title: 'SUPERVISION' },
	{ id: 'outcome', title: 'THE OUTCOME' }
];
