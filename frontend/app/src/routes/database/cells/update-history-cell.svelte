<script>
	let { network, formatDate } = $props();
</script>

{#if network.update_history && network.update_history.length > 0}
	<div class="flex flex-col gap-0.5">
		{#each [...network.update_history].reverse().slice(0, 3) as updateTime}
			<div class="text-xs text-muted-foreground">
				{formatDate(updateTime)}
			</div>
		{/each}
		{#if network.update_history.length > 3}
			<div class="text-xs text-muted-foreground/60 italic">
				+{network.update_history.length - 3} more
			</div>
		{/if}
	</div>
{:else}
	<div class="text-xs text-muted-foreground">-</div>
{/if}
