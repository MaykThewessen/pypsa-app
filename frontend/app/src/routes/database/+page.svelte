<script lang="ts">
	import { onMount } from 'svelte';
	import { goto } from '$app/navigation';
	import { browser } from '$app/environment';
	import { page } from '$app/stores';
	import { networks, admin } from '$lib/api/client.js';
	import { formatFileSize, formatDate, getDirectoryPath, getTagType, getTagColor, saveTablePref, buildOwnerOptions } from '$lib/utils.js';
	import { restoreTableState, buildTableURL, clampPage } from '$lib/table-url-state.js';
	import { Network, FolderOpen, Loader2 } from 'lucide-svelte';
	import { toast } from 'svelte-sonner';
	import * as Dialog from '$lib/components/ui/dialog';
	import * as Select from '$lib/components/ui/select';
	import { Label } from '$lib/components/ui/label';
	import Button from '$lib/components/ui/button/button.svelte';
	import PaginatedTable from '$lib/components/PaginatedTable.svelte';
	import { createColumns } from './components/columns.js';
	import { authStore } from '$lib/stores/auth.svelte.js';
	import EmptyState from '$lib/components/EmptyState.svelte';
	import TableSkeleton from '$lib/components/TableSkeleton.svelte';
	import type { Network as NetworkType, User, NetworkUpdate, ApiError, Visibility } from '$lib/types.js';
	import type { FilterState, FilterCategory } from '$lib/components/ui/filter-dialog';
	import type { ColumnDef, SortingState, VisibilityState, Row } from '@tanstack/table-core';

	// Components
	import ActionsBar from './components/ActionsBar.svelte';
	import FilterBar from '$lib/components/FilterBar.svelte';

	// Data state
	let networksList = $state<NetworkType[]>([]);
	let loading = $state(true);
	let totalNetworks = $state(0);
	let deletingId = $state<string | null>(null);
	let updatingVisibilityId = $state<string | null>(null);

	// Admin: owner reassignment dialog
	let editDialogOpen = $state(false);
	let editNetwork = $state<NetworkType | null>(null);
	let editOwner = $state<string | undefined>(undefined);
	let allUsers = $state<User[]>([]);
	let saving = $state(false);

	// Filter state (unified)
	let filters = $state<{ search: string; owners: Set<string> }>({
		search: '',
		owners: new Set()  // empty = all, contains IDs = filter to those
	});

	// Pagination state
	let currentPage = $state(1);
	let pageSize = $state(25);

	// Table state
	let sorting = $state<SortingState>([]);
	let columnVisibility = $state<VisibilityState>({});
	let expandedComponents = $state<Set<string>>(new Set());

	// Available owners from API (all unique owners across all visible networks)
	let availableOwners = $state<User[]>([]);

	// Derived: view state for conditional rendering
	const viewState = $derived.by(() => {
		if (loading) return 'loading';
		// Empty when no filters and no networks
		if (networksList.length === 0 && filters.owners.size === 0) return 'empty';
		// No matches when filters active but no results
		if (networksList.length === 0) return 'no-matches';
		return 'data';
	});

	const ownerOptions = $derived(buildOwnerOptions(availableOwners, authStore.user?.id));

	const filterCategories = $derived<FilterCategory[]>([
		{ key: 'owners', label: 'Owner', options: ownerOptions, condition: authStore.authEnabled && !!authStore.user },
	]);

	// Columns config - only recreate when authEnabled changes
	// Use getters for dynamic values to avoid recreating columns on every state change
	const columns = $derived.by(() => {
		const authEnabled = authStore.authEnabled ?? false;
		const isAdmin = authStore.isAdmin ?? false;
		return createColumns({
			getDirectoryPath,
			getTagType,
			getTagColor,
			formatFileSize,
			formatDate,
			handleDelete,
			toggleComponentsExpanded,
			getExpandedComponents: () => expandedComponents,
			handleVisibilityToggle,
			canEditNetwork,
			authEnabled,
			handleOwnerChange: isAdmin ? openOwnerDialog : undefined,
			getDeletingId: () => deletingId,
			getUpdatingVisibilityId: () => updatingVisibilityId
		});
	});

	function networkFilterFn(row: Row<NetworkType>, columnId: string, filterValue: string) {
		const searchStr = filterValue.toLowerCase();
		const network = row.original;
		if (network.filename?.toLowerCase().includes(searchStr)) return true;
		if (network.name?.toLowerCase().includes(searchStr)) return true;
		if (network.file_path?.toLowerCase().includes(searchStr)) return true;
		if (network.tags && Array.isArray(network.tags)) {
			return network.tags.some((tag) => {
				if (typeof tag === 'string') return tag.toLowerCase().includes(searchStr);
				if (typeof tag === 'object' && tag.name) return tag.name.toLowerCase().includes(searchStr);
				return false;
			});
		}
		return false;
	}

	const URL_FILTER_KEYS = ['owners'] as const;

	onMount(async () => {
		const state = restoreTableState($page.url.searchParams, 'networks', URL_FILTER_KEYS);
		currentPage = state.page;
		pageSize = state.pageSize;
		if (state.columnVisibility) columnVisibility = state.columnVisibility;
		if (state.filters.owners) filters.owners = state.filters.owners;

		await loadNetworks();
	});

	async function loadNetworks() {
		loading = true;
		try {
			const skip = (currentPage - 1) * pageSize;

			// Convert owner Set to API format (use 'me' for current user's ID)
			const ownerIds = filters.owners.size > 0
				? Array.from(filters.owners).map(id => id === authStore.user?.id ? 'me' : id)
				: null;

			const response = await networks.list(skip, pageSize, ownerIds);

			networksList = response.data;
			totalNetworks = response.meta.total;
			if (response.meta.owners) {
				availableOwners = response.meta.owners;
			}

			const clamped = clampPage(currentPage, pageSize, totalNetworks);
			if (clamped !== null) {
				currentPage = clamped;
				await updateURL();
				return loadNetworks();
			}
		} catch (err) {
			if ((err as ApiError).cancelled) return;
			toast.error((err as Error).message);
		} finally {
			loading = false;
		}
	}

	async function updateURL() {
		if (!browser) return;
		const url = buildTableURL(new URL(window.location.href), currentPage, pageSize, { owners: filters.owners }, URL_FILTER_KEYS);
		await goto(url.toString(), { replaceState: true, keepFocus: true, noScroll: true });
	}

	function handleSearchChange(search: string) {
		filters.search = search;
	}

	async function handleSetFilterChange(newFilters: FilterState) {
		filters.owners = newFilters.owners ?? new Set();
		currentPage = 1;
		await updateURL();
		await loadNetworks();
	}

	function handleColumnVisibilityChange(visibility: VisibilityState) {
		columnVisibility = visibility;
		saveTablePref('networks', 'columnVisibility', visibility);
	}

	async function handlePageChange(page: number) {
		currentPage = page;
		await updateURL();
		await loadNetworks();
		if (browser) window.scrollTo({ top: 0, behavior: 'smooth' });
	}

	async function handlePageSizeChange(size: number) {
		pageSize = size;
		currentPage = 1;
		saveTablePref('networks', 'pageSize', size);
		await updateURL();
		await loadNetworks();
	}

	async function handleUpload() {
		await loadNetworks();
	}

	async function handleDelete(networkId: string) {
		if (deletingId) return;
		if (!confirm('Are you sure you want to delete this network? This will remove both the database record and the file from disk. This action cannot be undone.')) {
			return;
		}
		deletingId = networkId;
		try {
			if (authStore.isAdmin) {
				await admin.deleteNetwork(networkId);
			} else {
				await networks.delete(networkId);
			}
			await loadNetworks();
		} catch (err) {
			if (!(err as ApiError).cancelled) toast.error((err as Error).message);
		} finally {
			deletingId = null;
		}
	}

	async function handleVisibilityToggle(networkId: string, newVisibility: Visibility) {
		if (updatingVisibilityId) return;
		updatingVisibilityId = networkId;
		try {
			if (authStore.isAdmin) {
				await admin.updateNetwork(networkId, { visibility: newVisibility });
			} else {
				await networks.updateVisibility(networkId, newVisibility);
			}
			await loadNetworks();
		} catch (err) {
			if (!(err as ApiError).cancelled) toast.error((err as Error).message);
		} finally {
			updatingVisibilityId = null;
		}
	}

	async function openOwnerDialog(network: NetworkType) {
		if (!authStore.isAdmin) return;
		editNetwork = network;
		editOwner = network.owner.id;
		editDialogOpen = true;
		if (allUsers.length === 0) {
			try {
				const response = await admin.listUsers(0, 1000);
				allUsers = response.data;
			} catch (err) {
				toast.error(`Failed to load users: ${(err as Error).message}`);
			}
		}
	}

	async function saveOwnerChange() {
		if (!editNetwork || saving) return;
		if (editOwner === editNetwork.owner.id) {
			editDialogOpen = false;
			return;
		}
		saving = true;
		try {
			await admin.updateNetwork(editNetwork.id, { user_id: editOwner });
			await loadNetworks();
			editDialogOpen = false;
		} catch (err) {
			toast.error(`Failed to update owner: ${(err as Error).message}`);
		} finally {
			saving = false;
		}
	}

	function viewNetwork(networkId: string) {
		goto(`/database/network?id=${networkId}`);
	}

	function toggleComponentsExpanded(networkId: string) {
		if (expandedComponents.has(networkId)) {
			expandedComponents.delete(networkId);
		} else {
			expandedComponents.add(networkId);
		}
		expandedComponents = expandedComponents;
	}

	function canEditNetwork(network: NetworkType) {
		if (!authStore.authEnabled || !authStore.user) return false;
		return authStore.isAdmin || network.owner.id === authStore.user.id;
	}

</script>

<div class="min-h-screen">
	<div class="max-w-[80rem] mx-auto py-8">
		<!-- Actions Bar (Scan + Upload) -->
		<ActionsBar onUpload={handleUpload} />

		<!-- Filter Bar (always visible) -->
		<FilterBar
			{filterCategories}
			filters={{ owners: filters.owners }}
			search={filters.search}
			onSearchChange={handleSearchChange}
			onFilterChange={handleSetFilterChange}
			{columns}
			{columnVisibility}
			onColumnVisibilityChange={handleColumnVisibilityChange}
		/>

		<!-- Content based on view state -->
		{#if viewState === 'loading'}
			<TableSkeleton rows={pageSize > 10 ? 10 : pageSize} />
		{:else if viewState === 'empty'}
			<EmptyState icon={Network} title="No Networks" description="Get started by uploading a network file." />
		{:else if viewState === 'no-matches'}
			<EmptyState icon={FolderOpen} title="No Results" description="No networks match your current filters." />
		{:else}
			<PaginatedTable
				mode="server"
				data={networksList}
				columns={columns as any}
				totalItems={totalNetworks}
				{currentPage}
				{pageSize}
				bind:sorting
				bind:columnVisibility
				globalFilter={filters.search}
				globalFilterFn={networkFilterFn as any}
				onPageChange={handlePageChange}
				onPageSizeChange={handlePageSizeChange}
				onRowClick={(network) => viewNetwork(network.id)}
			/>
		{/if}
	</div>
</div>

<!-- Admin: Change Owner Dialog -->
<Dialog.Root bind:open={editDialogOpen}>
	<Dialog.Content class="max-w-xs">
		{#if editNetwork}
			<Dialog.Header>
				<Dialog.Title>Change Owner</Dialog.Title>
				<Dialog.Description class="text-xs text-muted-foreground">
					{editNetwork.filename}
				</Dialog.Description>
			</Dialog.Header>
			<div class="space-y-4 py-4">
				<div class="space-y-2">
					<Label class="text-xs">Owner</Label>
					<Select.Root type="single" name="owner" bind:value={editOwner}>
						<Select.Trigger class="w-full">
							{@const ownerUser = allUsers.find((u) => u.id === editOwner)}
							{ownerUser?.username || 'Select owner...'}
						</Select.Trigger>
						<Select.Content>
							{#each allUsers as user}
								<Select.Item value={user.id}>{user.username}</Select.Item>
							{/each}
						</Select.Content>
					</Select.Root>
				</div>
			</div>
			<Dialog.Footer class="flex gap-2">
				<Button variant="outline" size="sm" onclick={() => (editDialogOpen = false)} disabled={saving}>
					Cancel
				</Button>
				<Button size="sm" onclick={saveOwnerChange} disabled={saving}>
					{#if saving}
						<Loader2 class="mr-1 size-4 animate-spin" />
					{/if}
					Save
				</Button>
			</Dialog.Footer>
		{/if}
	</Dialog.Content>
</Dialog.Root>
