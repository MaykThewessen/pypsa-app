<script>
	import * as Sidebar from '$lib/components/ui/sidebar';
	import { Switch } from '$lib/components/ui/switch';
	import { Button } from '$lib/components/ui/button';
	import { Checkbox } from '$lib/components/ui/checkbox';
	import { RotateCcw } from 'lucide-svelte';
	import {
		selectedCarriers,
		selectedCountries,
		showIndividualPlots,
		availableCarriers,
		availableCountries,
		toggleCarrier,
		toggleCountry,
		resetFilters
	} from '$lib/stores/networkPageStore';
</script>

<div class="flex flex-col h-full">
	<!-- Carriers Section -->
	<Sidebar.Group>
		<Sidebar.GroupLabel>Carriers / Sectors</Sidebar.GroupLabel>
		<Sidebar.GroupContent>
			{#if $availableCarriers.length === 0}
				<div class="text-sm text-muted-foreground text-center py-4">No carriers available</div>
			{:else}
				<div class="flex flex-col gap-2 max-h-[200px] overflow-y-auto pr-2">
					{#each $availableCarriers as carrier}
						<label class="flex items-center gap-2 cursor-pointer">
							<Checkbox
								checked={$selectedCarriers.has(carrier.name)}
								onCheckedChange={() => toggleCarrier(carrier.name)}
							/>
							<span class="text-sm">{carrier.nice_name || carrier.name}</span>
						</label>
					{/each}
				</div>
			{/if}
		</Sidebar.GroupContent>
	</Sidebar.Group>

	<!-- Plot Options Section -->
	<Sidebar.Group>
		<Sidebar.GroupLabel>Plot Options</Sidebar.GroupLabel>
		<Sidebar.GroupContent>
			<div class="flex items-center justify-between">
				<div class="flex flex-col gap-1">
					<span class="text-sm">Individual Plots</span>
					<span class="text-xs text-muted-foreground">Show each carrier separately</span>
				</div>
				<Switch
					checked={$showIndividualPlots}
					onCheckedChange={(checked) => ($showIndividualPlots = checked)}
				/>
			</div>
		</Sidebar.GroupContent>
	</Sidebar.Group>

	<!-- Countries Section -->
	<Sidebar.Group>
		<Sidebar.GroupLabel>Countries / Regions</Sidebar.GroupLabel>
		<Sidebar.GroupContent>
			{#if $availableCountries.length === 0}
				<div class="text-sm text-muted-foreground text-center py-4">No countries available</div>
			{:else}
				<div class="flex flex-col gap-2 max-h-[200px] overflow-y-auto pr-2">
					{#each $availableCountries as country}
						<label class="flex items-center gap-2 cursor-pointer">
							<Checkbox
								checked={$selectedCountries.has(country)}
								onCheckedChange={() => toggleCountry(country)}
							/>
							<span class="text-sm">{country}</span>
						</label>
					{/each}
				</div>
			{/if}
		</Sidebar.GroupContent>
	</Sidebar.Group>

	<!-- Reset Button -->
	<div class="mt-auto p-4">
		<Button variant="outline" size="sm" onclick={resetFilters} class="w-full">
			<RotateCcw class="h-4 w-4 mr-2" />
			Reset Filters
		</Button>
	</div>
</div>
