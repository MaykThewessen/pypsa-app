<script>
	import { onMount } from 'svelte';
	import { goto } from '$app/navigation';
	import { browser } from '$app/environment';
	import { page } from '$app/stores';
	import { networks } from '$lib/api/client.js';
	import Pagination from '$lib/components/Pagination.svelte';
	import { FolderOpen, Upload, Globe, FileUp, Network, CircleAlert, Search, Eye, EyeOff } from 'lucide-svelte';
	import { Button } from '$lib/components/ui/button';
	import * as DropdownMenu from '$lib/components/ui/dropdown-menu';
	import * as Empty from '$lib/components/ui/empty';
	import * as Alert from '$lib/components/ui/alert';
	import { Input } from '$lib/components/ui/input';
	import DataTable from './data-table.svelte';
	import { createColumns } from './columns.js';

	let networksList = $state([]);
	let loading = $state(true);
	let error = $state(null);
	let expandedComponents = $state(new Set()); // Track which networks have expanded components

	// Filter state
	let selectedTags = $state(new Set());
	let tagSearchQuery = $state('');

	// Pagination state
	let currentPage = $state(1);
	let pageSize = $state(25);
	let totalNetworks = $state(0);

	// Table state
	let sorting = $state([]);
	let columnVisibility = $state({});
	let globalFilter = $state('');

	onMount(async () => {
		// Load page size from localStorage
		if (browser) {
			const savedPageSize = localStorage.getItem('networksPageSize');
			if (savedPageSize) {
				pageSize = parseInt(savedPageSize);
			}
		}

		// Get page and size from URL
		const urlPage = $page.url.searchParams.get('page');
		const urlSize = $page.url.searchParams.get('size');

		if (urlPage) {
			const parsedPage = parseInt(urlPage);
			if (!isNaN(parsedPage) && parsedPage > 0) {
				currentPage = parsedPage;
			}
		}

		if (urlSize) {
			const parsedSize = parseInt(urlSize);
			if (!isNaN(parsedSize) && [1, 10, 25, 50, 100].includes(parsedSize)) {
				pageSize = parsedSize;
			}
		}
		await loadNetworks();
	});

	async function loadNetworks() {
		loading = true;
		error = null;
		try {
			// Calculate skip for pagination
			const skip = (currentPage - 1) * pageSize;

			// Fetch paginated data
			const response = await networks.list(skip, pageSize);

			networksList = response.data;
			totalNetworks = response.meta.total;

			// Validate current page doesn't exceed total pages
			const totalPages = Math.ceil(totalNetworks / pageSize);
			if (currentPage > totalPages && totalPages > 0) {
				// Redirect to last page
				currentPage = totalPages;
				await updateURL();
				return loadNetworks();
			}

			loading = false;
		} catch (err) {
			error = err.message;
			loading = false;
		}
	}

	async function updateURL() {
		if (!browser) return;

		const url = new URL(window.location.href);
		url.searchParams.set('page', currentPage.toString());
		url.searchParams.set('size', pageSize.toString());

		await goto(url.toString(), { replaceState: true, keepFocus: true, noScroll: true });
	}

	async function handlePageChange(page) {
		currentPage = page;
		await updateURL();
		await loadNetworks();

		// Scroll to top smoothly
		if (browser) {
			window.scrollTo({ top: 0, behavior: 'smooth' });
		}
	}

	async function handlePageSizeChange(size) {
		pageSize = size;
		currentPage = 1; // Reset to first page when changing page size

		// Save to localStorage
		if (browser) {
			localStorage.setItem('networksPageSize', size.toString());
		}

		await updateURL();
		await loadNetworks();
	}

	async function handleDelete(networkId) {
		if (!confirm('Are you sure you want to delete this network? This will remove both the database record and the file from disk. This action cannot be undone.')) {
			return;
		}

		try {
			await networks.delete(networkId);
			await loadNetworks();
		} catch (err) {
			error = err.message;
		}
	}

	function formatFileSize(bytes) {
		if (!bytes) return 'N/A';
		const mb = bytes / (1024 * 1024);
		return `${mb.toFixed(2)} MB`;
	}

	function formatDate(dateString) {
		if (!dateString) return 'N/A';
		const date = new Date(dateString);
		return date.toLocaleDateString() + ' ' + date.toLocaleTimeString();
	}

	function viewNetwork(networkId) {
		goto(`/network?id=${networkId}`);
	}

	function getComponentCount(network, primary, fallback = []) {
		const mapping = network?.components_count;
		if (!mapping) return 0;
		const keys = [primary, ...fallback];
		for (const key of keys) {
			if (key in mapping) {
				return mapping[key] ?? 0;
			}
		}
		return 0;
	}

	function getTotalComponents(network) {
		const counts = network?.components_count;
		if (!counts) return 0;

		// Sum up major components (excluding snapshots)
		const buses = getComponentCount(network, 'Bus', ['Buses', 'bus', 'buses']);
		const generators = getComponentCount(network, 'Generator', ['Generators', 'generator', 'generators']);
		const lines = getComponentCount(network, 'Line', ['Lines', 'line', 'lines']);
		const loads = getComponentCount(network, 'Load', ['Loads', 'load', 'loads']);

		return buses + generators + lines + loads;
	}

	function formatNumber(num) {
		if (num >= 1000) {
			return (num / 1000).toFixed(1) + 'k';
		}
		return num.toString();
	}

	function getDirectoryPath(fullPath) {
		if (!fullPath) return '';
		// Extract the part after /networks/
		const parts = fullPath.split('/networks/');
		const relativePath = parts.length > 1 ? parts[parts.length - 1] : fullPath;

		// Get just the directory portion (remove filename)
		const lastSlashIndex = relativePath.lastIndexOf('/');
		if (lastSlashIndex === -1) {
			// File is in root networks directory
			return '';
		}
		return relativePath.substring(0, lastSlashIndex + 1);
	}

	function getTagType(tag) {
		if (typeof tag === 'string') {
			return 'default';
		}
		const name = tag.name?.toLowerCase() || '';
		const url = tag.url?.toLowerCase() || '';

		// Check for config type
		if (name.includes('config') || name.endsWith('.yaml') || name.endsWith('.yml')) {
			return 'config';
		}

		// Check for version type (commit hash or version-like)
		if (url.includes('/commit/') || /^[a-f0-9]{7,}$/.test(name) || name === 'master' || name === 'main') {
			return 'version';
		}

		// Otherwise, assume it's a model/project
		return 'model';
	}

	function getTagColor(type) {
		switch (type) {
			case 'model':
				return 'tag-model';
			case 'version':
				return 'tag-version';
			case 'config':
				return 'tag-config';
			default:
				return 'tag-default';
		}
	}

	function handleUploadFromUrl() {
		alert('Upload from URL - Coming soon!');
	}

	function handleUploadFromLocal() {
		alert('Upload from local file - Coming soon!');
	}

	function toggleComponentsExpanded(networkId) {
		if (expandedComponents.has(networkId)) {
			expandedComponents.delete(networkId);
		} else {
			expandedComponents.add(networkId);
		}
		expandedComponents = expandedComponents; // Trigger reactivity
	}

	// Extract unique tags from all networks - reactive
	const allTags = $derived.by(() => {
		const tagsMap = new Map(); // Map tag name to tag object
		networksList.forEach(network => {
			if (network.tags && Array.isArray(network.tags)) {
				network.tags.forEach(tag => {
					const tagName = typeof tag === 'string' ? tag : tag.name;
					if (tagName && !tagsMap.has(tagName)) {
						tagsMap.set(tagName, tag);
					}
				});
			}
		});
		return Array.from(tagsMap.values()).sort((a, b) => {
			const aName = typeof a === 'string' ? a : a.name;
			const bName = typeof b === 'string' ? b : b.name;
			return aName.localeCompare(bName);
		});
	});

	// Filter tags based on search query
	const filteredTags = $derived(allTags.filter(tag => {
		const tagName = typeof tag === 'string' ? tag : tag.name;
		return tagName.toLowerCase().includes(tagSearchQuery.toLowerCase());
	}));

	// Toggle tag filter (works with tag name strings)
	function toggleTagFilter(tagName) {
		if (selectedTags.has(tagName)) {
			selectedTags.delete(tagName);
		} else {
			selectedTags.add(tagName);
		}
		selectedTags = selectedTags; // Trigger reactivity
	}

	// Filter networks based on selected tags (client-side filtering of current page only)
	const filteredNetworks = $derived(networksList.filter(network => {
		// If no tags selected, show all
		if (selectedTags.size === 0) return true;

		// Check if network has any of the selected tags
		const networkTags = network.tags?.map(tag =>
			typeof tag === 'string' ? tag : tag.name
		) || [];

		return Array.from(selectedTags).some(tag => networkTags.includes(tag));
	}));

	// Reset to page 1 when tag filters change
	let previousTagsSize = $state(0);
	$effect(() => {
		if (browser) {
			const currentSize = selectedTags.size;
			if (currentSize !== previousTagsSize) {
				previousTagsSize = currentSize;
				if (currentPage !== 1) {
					currentPage = 1;
					updateURL().then(() => loadNetworks());
				}
			}
		}
	});

	// Create columns for data table - use derived to ensure reactivity
	const columns = $derived(createColumns({
		getDirectoryPath,
		getTagType,
		getTagColor,
		formatFileSize,
		formatDate,
		handleDelete,
		toggleComponentsExpanded,
		expandedComponents
	}));
</script>

{#snippet toolbar()}
	<DropdownMenu.Root>
		<DropdownMenu.Trigger asChild>
			{#snippet child({ props })}
				<Button variant="default" size="sm" {...props}>
					<Upload class="h-4 w-4 mr-2" />
					Upload
				</Button>
			{/snippet}
		</DropdownMenu.Trigger>
		<DropdownMenu.Content align="end">
			<DropdownMenu.Item onclick={handleUploadFromUrl}>
				<Globe class="h-4 w-4 mr-2" />
				Upload from URL
			</DropdownMenu.Item>
			<DropdownMenu.Item onclick={handleUploadFromLocal}>
				<FileUp class="h-4 w-4 mr-2" />
				Upload from local file
			</DropdownMenu.Item>
		</DropdownMenu.Content>
	</DropdownMenu.Root>
{/snippet}

<div class="min-h-screen">
	<!-- Main Content -->
	<div>
		<div style="max-width: 80rem; margin: 0 auto; padding-top: 2rem; padding-bottom: 2rem;">
			{#if !loading && networksList.length > 0}
				<div class="mb-8 flex items-center justify-between gap-4">
					<div class="flex items-center gap-4 flex-1">
						<!-- Global Search -->
						<div class="relative max-w-sm flex-1">
							<Search class="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
							<Input
								type="text"
								placeholder="Search networks..."
								bind:value={globalFilter}
								class="pl-10"
							/>
						</div>

						<!-- Column Visibility Toggle -->
						<DropdownMenu.Root>
							<DropdownMenu.Trigger asChild>
								{#snippet child({ props })}
									<Button variant="outline" size="sm" {...props}>
										<Eye class="h-4 w-4 mr-2" />
										Columns
									</Button>
								{/snippet}
							</DropdownMenu.Trigger>
							<DropdownMenu.Content align="start">
								<DropdownMenu.Label>Toggle Columns</DropdownMenu.Label>
								<DropdownMenu.Separator />
								{#each columns as column}
									{#if column.accessorKey || column.id}
										{@const columnId = column.id || column.accessorKey}
										{@const isVisible = columnVisibility[columnId] !== false}
										<DropdownMenu.CheckboxItem
											checked={isVisible}
											onCheckedChange={(checked) => {
												columnVisibility = {
													...columnVisibility,
													[columnId]: checked
												};
											}}
										>
											{#if isVisible}
												<Eye class="h-4 w-4 mr-2" />
											{:else}
												<EyeOff class="h-4 w-4 mr-2" />
											{/if}
											{column.header}
										</DropdownMenu.CheckboxItem>
									{/if}
								{/each}
							</DropdownMenu.Content>
						</DropdownMenu.Root>
					</div>

					<!-- Upload Button -->
					<DropdownMenu.Root>
						<DropdownMenu.Trigger asChild>
							{#snippet child({ props })}
								<Button variant="default" size="sm" {...props}>
									<Upload class="h-4 w-4 mr-2" />
									Upload
								</Button>
							{/snippet}
						</DropdownMenu.Trigger>
						<DropdownMenu.Content align="end">
							<DropdownMenu.Item onclick={handleUploadFromUrl}>
								<Globe class="h-4 w-4 mr-2" />
								Upload from URL
							</DropdownMenu.Item>
							<DropdownMenu.Item onclick={handleUploadFromLocal}>
								<FileUp class="h-4 w-4 mr-2" />
								Upload from local file
							</DropdownMenu.Item>
						</DropdownMenu.Content>
					</DropdownMenu.Root>
				</div>
			{/if}

		{#if error}
			<Alert.Root variant="destructive">
				<CircleAlert class="size-4" />
				<Alert.Title>Error</Alert.Title>
				<Alert.Description>{error}</Alert.Description>
			</Alert.Root>
		{/if}

	{#if loading}
		<div class="flex justify-center items-center py-12">
			<div class="inline-block animate-spin rounded-full h-12 w-12 border-4 border-primary border-t-transparent"></div>
		</div>
	{:else if networksList.length === 0}
		<Empty.Root>
			<Empty.Header>
				<Empty.Media variant="icon">
					<Network />
				</Empty.Media>
				<Empty.Title>No Networks Found</Empty.Title>
				<Empty.Description>
					You haven't uploaded any PyPSA networks yet.
				</Empty.Description>
			</Empty.Header>
			<Empty.Content>
				<DropdownMenu.Root>
					<DropdownMenu.Trigger asChild>
						{#snippet child({ props })}
							<Button {...props}>
								<Upload class="h-4 w-4 mr-2" />
								Upload Network
							</Button>
						{/snippet}
					</DropdownMenu.Trigger>
					<DropdownMenu.Content>
						<DropdownMenu.Item onclick={handleUploadFromUrl}>
							<Globe class="h-4 w-4 mr-2" />
							Upload from URL
						</DropdownMenu.Item>
						<DropdownMenu.Item onclick={handleUploadFromLocal}>
							<FileUp class="h-4 w-4 mr-2" />
							Upload from local file
						</DropdownMenu.Item>
					</DropdownMenu.Content>
				</DropdownMenu.Root>
			</Empty.Content>
		</Empty.Root>
	{:else if filteredNetworks.length === 0}
		<Empty.Root>
			<Empty.Header>
				<Empty.Media variant="icon">
					<FolderOpen />
				</Empty.Media>
				<Empty.Title>No Networks Match Filters</Empty.Title>
				<Empty.Description>
					No networks match your current filter selections. Try adjusting your filters to see more results.
				</Empty.Description>
			</Empty.Header>
		</Empty.Root>
	{:else}
		<DataTable
			data={filteredNetworks}
			{columns}
			totalItems={totalNetworks}
			{pageSize}
			bind:sorting
			bind:columnVisibility
			bind:globalFilter
			onRowClick={(network) => viewNetwork(network.id)}
		/>

			<!-- Pagination -->
			<div class="mt-6">
				<Pagination
					{currentPage}
					{pageSize}
					totalItems={totalNetworks}
					onPageChange={handlePageChange}
					onPageSizeChange={handlePageSizeChange}
				/>
			</div>

			<!-- Filter info (if filters active) -->
			{#if selectedTags.size > 0 && filteredNetworks.length !== networksList.length}
				<div class="mt-4 text-sm text-muted-foreground italic text-center">
					Note: Showing {filteredNetworks.length} of {networksList.length} networks on this page that match your filters.
					Tag filters only apply to the current page.
				</div>
			{/if}
		{/if}
		</div>
	</div>
</div>
