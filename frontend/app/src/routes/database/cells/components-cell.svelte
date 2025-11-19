<script>
	let { network, isExpanded, toggleComponentsExpanded } = $props();
</script>

<div class="flex flex-wrap gap-1">
	{#if network.components_count && Object.keys(network.components_count).length > 0}
		{@const allComponents = Object.entries(network.components_count)}
		{@const componentsToShow = isExpanded ? allComponents : allComponents.slice(0, 3)}
		{@const remainingCount = allComponents.length - 3}

		{#each componentsToShow as [component, count]}
			<span class="inline-flex items-center gap-1 bg-muted px-2 py-0.5 rounded text-xs">
				<span class="text-muted-foreground">{component}:</span>
				<span class="font-semibold">{count.toLocaleString()}</span>
			</span>
		{/each}

		{#if allComponents.length > 3}
			<button
				onclick={() => toggleComponentsExpanded(network.id)}
				class="inline-flex items-center gap-1 bg-muted hover:bg-muted/80 px-2 py-0.5 rounded text-xs transition-colors cursor-pointer"
			>
				{#if isExpanded}
					Show less
				{:else}
					+{remainingCount} more
				{/if}
			</button>
		{/if}
	{:else}
		<span class="text-xs text-muted-foreground">No data</span>
	{/if}
</div>
