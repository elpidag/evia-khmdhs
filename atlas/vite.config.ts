import { defineConfig } from 'vitest/config';
import adapter from '@sveltejs/adapter-node';
import { sveltekit } from '@sveltejs/kit/vite';
import { mdsvex } from 'mdsvex';
import { tagParagraphs, figureMarkers } from './scripts/remark-tag-paragraphs';

export default defineConfig({
	plugins: [
		sveltekit({
			// the narration lives in markdown the author edits (user, 2026-08-27):
			// src/content/**/*.md compile to components through mdsvex
			extensions: ['.svelte', '.md'],
			// figureMarkers wraps the author's plain `[FIGURE nn: name]` markers so
			// they hide in the prose; tagParagraphs restores the <p> around a
			// paragraph that begins with a tag — scripts/remark-tag-paragraphs.ts
			preprocess: [
				mdsvex({ extensions: ['.md'], remarkPlugins: [figureMarkers, tagParagraphs] })
			],
			compilerOptions: {
				// Force runes mode for the project, except for libraries. Can be removed in svelte 6.
				runes: ({ filename }) => (filename.split(/[/\\]/).includes('node_modules') ? undefined : true)
			},
			adapter: adapter(),
			alias: { $content: 'src/content' }
		})
	],
	server: {
		// Browser-originated /api and /pdf requests go to the Flask API in dev.
		// SSR-originated fetches are routed by handleFetch in src/hooks.server.ts.
		proxy: {
			'/api': 'http://127.0.0.1:5050',
			'/pdf': 'http://127.0.0.1:5050'
		},
		// pre-transform routes + lib so first navigations don't pay the
		// on-demand compile waterfall (dev only; production is bundled)
		warmup: {
			clientFiles: ['./src/routes/**/*.svelte', './src/lib/**/*.svelte', './src/lib/**/*.ts']
		}
	},
	test: {
		expect: { requireAssertions: true },
		projects: [
			{
				extends: './vite.config.ts',
				test: {
					name: 'server',
					environment: 'node',
					include: ['src/**/*.{test,spec}.{js,ts}'],
					exclude: ['src/**/*.svelte.{test,spec}.{js,ts}']
				}
			}
		]
	}
});
