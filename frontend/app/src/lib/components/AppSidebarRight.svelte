<script>
	import NavNetworkFilters from './sidebar/NavNetworkFilters.svelte';
	import * as Sidebar from '$lib/components/ui/sidebar';
	import { SlidersHorizontal } from 'lucide-svelte';
</script>

<Sidebar.Root side="right" collapsible="icon">
	<Sidebar.Header>
		<Sidebar.Menu>
			<Sidebar.MenuItem>
				<Sidebar.MenuButton size="lg" class="justify-start">
					{#snippet child({ props })}
						<div class="flex items-center gap-2" {...props}>
							<SlidersHorizontal class="h-5 w-5 shrink-0" />
							<span class="font-semibold">Filters & Options</span>
						</div>
					{/snippet}
				</Sidebar.MenuButton>
			</Sidebar.MenuItem>
		</Sidebar.Menu>
	</Sidebar.Header>

	<Sidebar.Content>
		<NavNetworkFilters />
	</Sidebar.Content>

	<Sidebar.Rail />
</Sidebar.Root>
