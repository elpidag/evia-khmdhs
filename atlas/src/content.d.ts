// markdown narration (mdsvex): each src/content/**/*.md compiles to a
// component. A global declaration file — inside app.d.ts (a module) the
// same lines would be an augmentation and resolve nothing.
declare module '*.md' {
	import type { Component } from 'svelte';
	const component: Component;
	export default component;
}
