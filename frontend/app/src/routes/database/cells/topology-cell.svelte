<script>
	let { network } = $props();
</script>

{#if network.topology_svg}
	<div class="topology-icon w-16 h-12 flex items-center justify-center overflow-hidden rounded-lg border border-border">
		{@html network.topology_svg}
	</div>
{:else}
	<div class="w-16 h-12 flex items-center justify-center bg-muted/30 rounded-lg border border-border text-muted-foreground">
		<svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
			<circle cx="12" cy="12" r="2"></circle>
			<path d="M12 2v4m0 12v4M6.34 6.34l2.83 2.83m5.66 5.66l2.83 2.83m-11.32 0l2.83-2.83m5.66-5.66l2.83-2.83"></path>
		</svg>
	</div>
{/if}
