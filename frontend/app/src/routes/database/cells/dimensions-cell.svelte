<script>
	import { Clock, CalendarRange, Waypoints } from 'lucide-svelte';

	let { network } = $props();
</script>

<div class="flex flex-col gap-1">
	{#if network.dimensions_count}
		{#if network.dimensions_count.timesteps}
			<div class="inline-flex items-center gap-1.5 text-xs">
				<Clock size={14} class="text-muted-foreground" />
				<span class="font-semibold">{network.dimensions_count.timesteps.toLocaleString()}</span>
			</div>
		{/if}
		{#if network.dimensions_count.periods}
			<div class="inline-flex items-center gap-1.5 text-xs">
				<CalendarRange size={14} class="text-muted-foreground" />
				<span class="font-semibold">{network.dimensions_count.periods.toLocaleString()}</span>
			</div>
		{/if}
		{#if network.dimensions_count.scenarios}
			<div class="inline-flex items-center gap-1.5 text-xs">
				<Waypoints size={14} class="text-muted-foreground" />
				<span class="font-semibold">{network.dimensions_count.scenarios.toLocaleString()}</span>
			</div>
		{/if}
	{:else}
		<span class="text-xs text-muted-foreground">-</span>
	{/if}
</div>
