<script lang="ts">
	import { onMount } from 'svelte';
	import { authStore } from '$lib/stores/auth.svelte.js';
	import { admin } from '$lib/api/client.js';
	import { formatDate } from '$lib/utils.js';
	import Button from '$lib/components/ui/button/button.svelte';
	import * as Avatar from '$lib/components/ui/avatar';
	import * as Dialog from '$lib/components/ui/dialog';
	import { Badge } from '$lib/components/ui/badge';
	import FilterBar from '$lib/components/FilterBar.svelte';
	import type { FilterState, FilterCategory } from '$lib/components/ui/filter-dialog';
	import PaginatedTable from '$lib/components/PaginatedTable.svelte';
	import TableSkeleton from '$lib/components/TableSkeleton.svelte';
	import { createColumns } from './user-columns.js';
	import { toast } from 'svelte-sonner';
	import type { User } from '$lib/types.js';
	import type { SortingState } from '@tanstack/table-core';

	let { createOpen = $bindable(false) }: { createOpen?: boolean } = $props();

	const roleOptions = ['admin', 'user', 'bot', 'pending'];

	let allUsers = $state<User[]>([]);
	let loading = $state(true);
	let filters = $state<FilterState>({});
	let selectedUser = $state<User | null>(null);
	let dialogOpen = $state(false);
	let allPermissions = $state<string[]>([]);
	let rolePermissions = $state<Record<string, string[]>>({});
	let sorting = $state<SortingState>([]);
	let newUsername = $state('');
	let newUserRole = $state('bot');
	let newAvatarUrl = $state('');
	let creatingUser = $state(false);

	// Delete confirmation
	let confirmDeleteOpen = $state(false);
	let userToDelete = $state<User | null>(null);

	const filterCategories: FilterCategory[] = [
		{
			key: 'roles',
			label: 'Role',
			options: roleOptions.map((r) => ({ id: r, label: r }))
		}
	];

	let users = $derived(
		filters.roles?.size ? allUsers.filter((u) => filters.roles.has(u.role)) : allUsers
	);

	const columns = $derived(
		createColumns({
			onApprove: approveUser,
			onOpenPermissions: openPermissions
		})
	);

	onMount(async () => {
		await Promise.all([loadUsers(), loadPermissions()]);
	});

	async function loadPermissions() {
		try {
			const response = await admin.getPermissions();
			allPermissions = response.permissions as string[];
			rolePermissions = response.role_permissions as Record<string, string[]>;
		} catch (err) {
			toast.error(`Failed to load permissions: ${(err as Error).message}`);
		}
	}

	async function loadUsers() {
		loading = true;
		try {
			const response = await admin.listUsers(0, 100);
			allUsers = response.data;
		} catch (err) {
			toast.error((err as Error).message);
		} finally {
			loading = false;
		}
	}

	async function approveUser(userId: string) {
		try {
			await admin.approveUser(userId);
			await loadUsers();
		} catch (err) {
			toast.error((err as Error).message);
		}
	}

	async function updateRole(userId: string, newRole: string) {
		try {
			await admin.updateUserRole(userId, newRole);
			await loadUsers();
		} catch (err) {
			toast.error((err as Error).message);
		}
	}

	async function deleteUser() {
		if (!userToDelete) return;
		try {
			await admin.deleteUser(userToDelete.id);
			confirmDeleteOpen = false;
			dialogOpen = false;
			userToDelete = null;
			await loadUsers();
		} catch (err) {
			toast.error((err as Error).message);
		}
	}

	function openPermissions(user: User) {
		selectedUser = user;
		dialogOpen = true;
	}

	async function createUser() {
		if (!newUsername.trim()) return;
		creatingUser = true;
		try {
			await admin.createUser(
				newUsername.trim(),
				newUserRole,
				newAvatarUrl.trim() || undefined
			);
			newUsername = '';
			newUserRole = 'bot';
			newAvatarUrl = '';
			createOpen = false;
			await loadUsers();
		} catch (err) {
			toast.error((err as Error).message);
		} finally {
			creatingUser = false;
		}
	}
</script>

<FilterBar
	{filterCategories}
	{filters}
	onFilterChange={(f) => (filters = f)}
/>

{#if loading}
	<TableSkeleton rows={5} columns={6} />
{:else if users.length === 0}
	<p class="text-muted-foreground">No users found.</p>
{:else}
	<PaginatedTable
		data={users}
		columns={columns as any}
		bind:sorting
		onRowClick={(user) => openPermissions(user)}
	/>
{/if}

<!-- Permissions Dialog -->
<Dialog.Root bind:open={dialogOpen}>
	<Dialog.Content class="max-w-xs">
		{#if selectedUser}
			{@const userRole = selectedUser.role}
			<Dialog.Header>
				<Dialog.Title class="flex items-center gap-2 text-sm">
					<Avatar.Root class="size-6">
						<Avatar.Image src={selectedUser.avatar_url} alt={selectedUser.username} />
						<Avatar.Fallback class="text-xs">
							{selectedUser.username.substring(0, 2).toUpperCase()}
						</Avatar.Fallback>
					</Avatar.Root>
					{selectedUser.username}
				</Dialog.Title>
			</Dialog.Header>
			<div class="space-y-3 text-xs">
				<div class="space-y-1 text-muted-foreground">
					<p>{selectedUser.email || 'No email'}</p>
					<p>Created: {formatDate(selectedUser.created_at)}</p>
					<p>Last login: {formatDate(selectedUser.last_login)}</p>
				</div>
				<div class="flex items-center justify-between">
					<span class="text-muted-foreground">Role</span>
					{#if selectedUser.id === authStore.user?.id}
						<Badge variant="outline" class="text-xs">{userRole} (you)</Badge>
					{:else}
						<select
							class="rounded border bg-background px-2 py-1 text-xs"
							value={userRole}
							onchange={(e: Event) =>
								updateRole(
									selectedUser!.id,
									(e.target as HTMLSelectElement).value
								)}
						>
							<option value="admin">admin</option>
							<option value="user">user</option>
							<option value="bot">bot</option>
							<option value="pending">pending</option>
						</select>
					{/if}
				</div>
				<div class="space-y-1">
					<span class="text-muted-foreground">Permissions</span>
					<div class="flex flex-wrap gap-1">
						{#each allPermissions as perm}
							{@const hasPerm = selectedUser.permissions?.includes(perm)}
							<code
								class="rounded px-1.5 py-0.5 text-xs {hasPerm
									? 'bg-muted'
									: 'bg-muted/30 text-muted-foreground line-through'}"
								>{perm}</code
							>
						{/each}
					</div>
				</div>
				{#if selectedUser.id !== authStore.user?.id}
					<button
						class="text-destructive hover:underline"
						onclick={() => {
							userToDelete = selectedUser;
							confirmDeleteOpen = true;
						}}
					>
						Delete user
					</button>
				{/if}
			</div>
		{/if}
	</Dialog.Content>
</Dialog.Root>

<!-- Delete Confirmation Dialog -->
<Dialog.Root bind:open={confirmDeleteOpen}>
	<Dialog.Content class="max-w-xs">
		<Dialog.Header>
			<Dialog.Title>Delete User</Dialog.Title>
			<Dialog.Description>
				Are you sure you want to delete user "{userToDelete?.username}"? This action cannot
				be undone.
			</Dialog.Description>
		</Dialog.Header>
		<div class="flex justify-end gap-2">
			<Button variant="outline" size="sm" onclick={() => (confirmDeleteOpen = false)}>
				Cancel
			</Button>
			<Button variant="destructive" size="sm" onclick={deleteUser}>Delete</Button>
		</div>
	</Dialog.Content>
</Dialog.Root>

<!-- Create User Dialog -->
<Dialog.Root bind:open={createOpen}>
	<Dialog.Content class="max-w-xs">
		<Dialog.Header>
			<Dialog.Title>Create User</Dialog.Title>
			<Dialog.Description>Create a new user account.</Dialog.Description>
		</Dialog.Header>
		<div class="space-y-4">
			<div class="space-y-2">
				<label for="new-username" class="text-sm font-medium">Username</label>
				<input
					id="new-username"
					type="text"
					class="w-full rounded-md border bg-background px-3 py-2 text-sm"
					placeholder="username"
					bind:value={newUsername}
					onkeydown={(e: KeyboardEvent) => {
						if (e.key === 'Enter') createUser();
					}}
				/>
			</div>
			<div class="space-y-2">
				<label for="new-user-role" class="text-sm font-medium">Role</label>
				<select
					id="new-user-role"
					class="w-full rounded-md border bg-background px-3 py-2 text-sm"
					bind:value={newUserRole}
				>
					<option value="bot">bot</option>
				</select>
				<p class="text-xs text-muted-foreground">
					Only bot users can be created via the admin panel.
				</p>
			</div>
			<div class="space-y-2">
				<label for="new-avatar-url" class="text-sm font-medium"
					>Avatar URL
					<span class="text-muted-foreground font-normal">(optional)</span></label
				>
				<input
					id="new-avatar-url"
					type="url"
					class="w-full rounded-md border bg-background px-3 py-2 text-sm"
					placeholder="https://github.com/user.png"
					bind:value={newAvatarUrl}
				/>
			</div>
			<div class="flex justify-end gap-2">
				<Button variant="outline" size="sm" onclick={() => (createOpen = false)}
					>Cancel</Button
				>
				<Button
					size="sm"
					disabled={!newUsername.trim() || creatingUser}
					onclick={createUser}
				>
					{creatingUser ? 'Creating...' : 'Create'}
				</Button>
			</div>
		</div>
	</Dialog.Content>
</Dialog.Root>
