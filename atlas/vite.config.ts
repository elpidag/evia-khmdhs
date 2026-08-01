import { defineConfig } from 'vitest/config';
import adapter from '@sveltejs/adapter-node';
import { sveltekit } from '@sveltejs/kit/vite';

export default defineConfig({
	plugins: [
		sveltekit({
			compilerOptions: {
				// Force runes mode for the project, except for libraries. Can be removed in svelte 6.
				runes: ({ filename }) => (filename.split(/[/\\]/).includes('node_modules') ? undefined : true)
			},
			adapter: adapter()
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
