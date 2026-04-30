<script lang="ts">
	import type { RunSummary } from '$lib/types.js';
	import StatusBadge from './StatusBadge.svelte';

	let { run }: { run: RunSummary } = $props();
</script>

<StatusBadge status={run.status} />
