<script lang="ts">
	import { onMount } from 'svelte';
	import { admin } from '$lib/api/client.js';
	import { Server, Plus, Trash2, Loader2 } from 'lucide-svelte';
	import Button from '$lib/components/ui/button/button.svelte';
	import * as Dialog from '$lib/components/ui/dialog';
	import FilterBar from '$lib/components/FilterBar.svelte';
	import type { FilterState, FilterCategory } from '$lib/components/ui/filter-dialog';
	import PaginatedTable from '$lib/components/PaginatedTable.svelte';
	import TableSkeleton from '$lib/components/TableSkeleton.svelte';
	import { createColumns } from './backend-columns.js';
	import { toast } from 'svelte-sonner';
	import type { Backend, User } from '$lib/types.js';
	import type { SortingState } from '@tanstack/table-core';

	let allBackends = $state<Backend[]>([]);
	let filters = $state<FilterState>({});

	const filterCategories: FilterCategory[] = [
		{
			key: 'status',
			label: 'Status',
			options: [
				{ id: 'active', label: 'Active' },
				{ id: 'inactive', label: 'Inactive' }
			]
		}
	];

	let backends = $derived(
		filters.status?.size
			? allBackends.filter((b) =>
					filters.status.has(b.is_active ? 'active' : 'inactive')
				)
			: allBackends
	);
	let loading = $state(true);
	let sorting = $state<SortingState>([]);

	// User assignment dialog
	let selectedBackend = $state<Backend | null>(null);
	let assignedUsers = $state<User[]>([]);
	let allUsers = $state<User[]>([]);
	let dialogOpen = $state(false);
	let usersLoading = $state(false);

	const columns = $derived(
		createColumns({
			onManageUsers: openUserDialog
		})
	);

	onMount(async () => {
		await loadBackends();
	});

	async function loadBackends() {
		loading = true;
		try {
			allBackends = await admin.listBackends();
		} catch (err) {
			toast.error((err as Error).message);
		} finally {
			loading = false;
		}
	}

	async function openUserDialog(backend: Backend) {
		selectedBackend = backend;
		dialogOpen = true;
		usersLoading = true;
		try {
			const [users, assigned] = await Promise.all([
				admin.listUsers(0, 200),
				admin.listBackendUsers(backend.id)
			]);
			allUsers = users.data;
			assignedUsers = assigned;
		} catch (err) {
			toast.error((err as Error).message);
		} finally {
			usersLoading = false;
		}
	}

	async function assignUser(userId: string) {
		if (!selectedBackend) return;
		try {
			await admin.assignUserToBackend(selectedBackend.id, userId);
			assignedUsers = await admin.listBackendUsers(selectedBackend.id);
			toast.success('User assigned');
		} catch (err) {
			toast.error((err as Error).message);
		}
	}

	async function unassignUser(userId: string) {
		if (!selectedBackend) return;
		try {
			await admin.unassignUserFromBackend(selectedBackend.id, userId);
			assignedUsers = await admin.listBackendUsers(selectedBackend.id);
			toast.success('User removed');
		} catch (err) {
			toast.error((err as Error).message);
		}
	}

	function isAssigned(userId: string): boolean {
		return assignedUsers.some((u) => u.id === userId);
	}

	let unassignedUsers = $derived(allUsers.filter((u) => !isAssigned(u.id)));
</script>

<FilterBar
	{filterCategories}
	{filters}
	onFilterChange={(f) => (filters = f)}
/>

{#if loading}
	<TableSkeleton rows={3} columns={5} />
{:else if backends.length === 0}
	<div class="rounded-md border p-6 text-center text-muted-foreground">
		<Server class="mx-auto mb-2 size-8" />
		<p>No backends configured.</p>
		<p class="mt-1 text-xs">
			Set <code>SNAKEDISPATCH_BACKENDS</code> to register backends.
		</p>
	</div>
{:else}
	<PaginatedTable
		data={backends}
		columns={columns as any}
		bind:sorting
	/>
{/if}

<!-- User Assignment Dialog -->
<Dialog.Root bind:open={dialogOpen}>
	<Dialog.Content class="max-w-md">
		{#if selectedBackend}
			<Dialog.Header>
				<Dialog.Title class="flex items-center gap-2">
					<Server class="size-5" />
					{selectedBackend.name}
				</Dialog.Title>
				<Dialog.Description>Manage user assignments for this backend.</Dialog.Description>
			</Dialog.Header>

			{#if usersLoading}
				<div class="flex items-center gap-2 py-4 text-muted-foreground text-sm">
					<Loader2 class="size-4 animate-spin" />
					Loading users...
				</div>
			{:else}
				<div class="space-y-4">
					<div>
						<h3 class="mb-2 text-sm font-medium">
							Assigned Users ({assignedUsers.length})
						</h3>
						{#if assignedUsers.length === 0}
							<p class="text-xs text-muted-foreground">
								No users assigned. Admins always have access.
							</p>
						{:else}
							<div class="space-y-1">
								{#each assignedUsers as user}
									<div
										class="flex items-center justify-between rounded-md border px-3 py-2"
									>
										<span class="text-sm">{user.username}</span>
										<Button
											variant="ghost"
											size="icon"
											class="size-7"
											onclick={() => unassignUser(user.id)}
											title="Remove"
										>
											<Trash2 class="size-3.5 text-destructive" />
										</Button>
									</div>
								{/each}
							</div>
						{/if}
					</div>

					{#if unassignedUsers.length > 0}
						<div>
							<h3 class="mb-2 text-sm font-medium">Add User</h3>
							<div class="max-h-48 space-y-1 overflow-y-auto">
								{#each unassignedUsers as user}
									<div
										class="flex items-center justify-between rounded-md border px-3 py-2"
									>
										<span class="text-sm">{user.username}</span>
										<Button
											variant="ghost"
											size="icon"
											class="size-7"
											onclick={() => assignUser(user.id)}
											title="Assign"
										>
											<Plus class="size-3.5" />
										</Button>
									</div>
								{/each}
							</div>
						</div>
					{/if}
				</div>
			{/if}
		{/if}
	</Dialog.Content>
</Dialog.Root>
