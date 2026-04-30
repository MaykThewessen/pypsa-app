<script lang="ts">
	import { onMount } from 'svelte';
	import { admin, apiKeys } from '$lib/api/client.js';
	import { Copy } from 'lucide-svelte';
	import Button from '$lib/components/ui/button/button.svelte';
	import * as Dialog from '$lib/components/ui/dialog';
	import PaginatedTable from '$lib/components/PaginatedTable.svelte';
	import TableSkeleton from '$lib/components/TableSkeleton.svelte';
	import FilterBar from '$lib/components/FilterBar.svelte';
	import type { FilterState, FilterCategory } from '$lib/components/ui/filter-dialog';
	import { createColumns } from './api-key-columns.js';
	import { toast } from 'svelte-sonner';
	import type { User, ApiKey } from '$lib/types.js';
	import type { SortingState } from '@tanstack/table-core';

	let { createOpen = $bindable(false) }: { createOpen?: boolean } = $props();

	// Reset created key when dialog opens
	$effect(() => {
		if (createOpen) createdKey = null;
	});

	let allKeys = $state<ApiKey[]>([]);
	let keysLoading = $state(true);
	let filters = $state<FilterState>({});
	let newKeyName = $state('');
	let newKeyUserId = $state('');
	let newKeyExpiryDays = $state(90);
	let creatingKey = $state(false);
	let createdKey = $state<string | null>(null);
	let sorting = $state<SortingState>([]);

	let botUsers = $state<User[]>([]);

	// Delete confirmation
	let confirmDeleteOpen = $state(false);
	let keyToDelete = $state<ApiKey | null>(null);

	const filterCategories = $derived<FilterCategory[]>([
		{
			key: 'users',
			label: 'Bot User',
			options: botUsers.map((u) => ({ id: u.id, label: u.username }))
		}
	]);

	let keys = $derived(
		filters.users?.size
			? allKeys.filter((k) => filters.users.has(k.owner.id))
			: allKeys
	);

	const columns = $derived(
		createColumns({
			onDelete: (key) => {
				keyToDelete = key;
				confirmDeleteOpen = true;
			}
		})
	);

	onMount(async () => {
		await Promise.all([loadApiKeys(), loadBotUsers()]);
	});

	async function loadBotUsers() {
		try {
			const response = await admin.listUsers(0, 100, 'bot');
			botUsers = response.data;
		} catch (err) {
			toast.error(`Failed to load bot users: ${(err as Error).message}`);
		}
	}

	async function loadApiKeys() {
		keysLoading = true;
		try {
			allKeys = await apiKeys.list();
		} catch (err) {
			toast.error(`Failed to load API keys: ${(err as Error).message}`);
		} finally {
			keysLoading = false;
		}
	}

	async function createApiKey() {
		if (!newKeyName.trim() || !newKeyUserId) return;
		creatingKey = true;
		try {
			const result = await apiKeys.create(newKeyName.trim(), newKeyExpiryDays, newKeyUserId);
			createdKey = result.key ?? null;
			newKeyName = '';
			newKeyUserId = '';
			newKeyExpiryDays = 90;
			if (!createdKey) {
				createOpen = false;
			}
			await loadApiKeys();
		} catch (err) {
			toast.error((err as Error).message);
		} finally {
			creatingKey = false;
		}
	}

	async function deleteApiKey() {
		if (!keyToDelete) return;
		try {
			await apiKeys.delete(keyToDelete.id);
			confirmDeleteOpen = false;
			keyToDelete = null;
			await loadApiKeys();
		} catch (err) {
			toast.error((err as Error).message);
		}
	}

	async function copyToClipboard(text: string) {
		try {
			await navigator.clipboard.writeText(text);
			toast.success('Copied to clipboard');
		} catch {
			toast.error('Failed to copy to clipboard');
		}
	}
</script>

<FilterBar
	{filterCategories}
	{filters}
	onFilterChange={(f) => (filters = f)}
/>

{#if keysLoading}
	<TableSkeleton rows={3} columns={7} />
{:else if keys.length === 0}
	<p class="text-muted-foreground text-sm">No API keys created yet.</p>
{:else}
	<PaginatedTable
		data={keys}
		columns={columns as any}
		bind:sorting
	/>
{/if}

<!-- Delete Confirmation Dialog -->
<Dialog.Root bind:open={confirmDeleteOpen}>
	<Dialog.Content class="max-w-xs">
		<Dialog.Header>
			<Dialog.Title>Delete API Key</Dialog.Title>
			<Dialog.Description>
				Are you sure you want to delete API key "{keyToDelete?.name}"? This action cannot be
				undone.
			</Dialog.Description>
		</Dialog.Header>
		<div class="flex justify-end gap-2">
			<Button variant="outline" size="sm" onclick={() => (confirmDeleteOpen = false)}>
				Cancel
			</Button>
			<Button variant="destructive" size="sm" onclick={deleteApiKey}>Delete</Button>
		</div>
	</Dialog.Content>
</Dialog.Root>

<!-- Create API Key Dialog -->
<Dialog.Root bind:open={createOpen}>
	<Dialog.Content class="max-w-sm">
		<Dialog.Header>
			<Dialog.Title>Create API Key</Dialog.Title>
			<Dialog.Description>Create a new API key linked to a bot user.</Dialog.Description>
		</Dialog.Header>

		{#if createdKey}
			<div class="space-y-4">
				<div class="rounded-md border border-green-500/30 bg-green-500/10 p-3">
					<p class="mb-2 text-sm font-medium">API key created successfully!</p>
					<p class="mb-2 text-xs text-muted-foreground">
						Copy this key now. You won't be able to see it again.
					</p>
					<div class="flex items-center gap-2">
						<code class="flex-1 break-all rounded bg-muted px-2 py-1 text-xs"
							>{createdKey}</code
						>
						<Button
							variant="outline"
							size="icon"
							class="size-8 shrink-0"
							onclick={() => copyToClipboard(createdKey!)}
							title="Copy"
						>
							<Copy class="size-4" />
						</Button>
					</div>
				</div>
				<div class="flex justify-end">
					<Button
						size="sm"
						onclick={() => {
							createdKey = null;
							createOpen = false;
						}}>Done</Button
					>
				</div>
			</div>
		{:else}
			<div class="space-y-4">
				<div class="space-y-2">
					<label for="key-name" class="text-sm font-medium">Name</label>
					<input
						id="key-name"
						type="text"
						class="w-full rounded-md border bg-background px-3 py-2 text-sm"
						placeholder="CI/CD Pipeline"
						bind:value={newKeyName}
					/>
				</div>
				<div class="space-y-2">
					<label for="key-user" class="text-sm font-medium">User</label>
					<select
						id="key-user"
						class="w-full rounded-md border bg-background px-3 py-2 text-sm"
						bind:value={newKeyUserId}
					>
						<option value="">Select a user...</option>
						{#each botUsers as bot}
							<option value={bot.id}>{bot.username}</option>
						{/each}
					</select>
					{#if botUsers.length === 0}
						<p class="text-xs text-muted-foreground">
							No bot users available. Create one first.
						</p>
					{/if}
				</div>
				<div class="space-y-2">
					<label for="key-expiry" class="text-sm font-medium">Expires in (days)</label>
					<input
						id="key-expiry"
						type="number"
						class="w-full rounded-md border bg-background px-3 py-2 text-sm"
						min="1"
						max="365"
						bind:value={newKeyExpiryDays}
					/>
				</div>
				<div class="flex justify-end gap-2">
					<Button variant="outline" size="sm" onclick={() => (createOpen = false)}
						>Cancel</Button
					>
					<Button
						size="sm"
						disabled={!newKeyName.trim() || !newKeyUserId || creatingKey}
						onclick={createApiKey}
					>
						{creatingKey ? 'Creating...' : 'Create'}
					</Button>
				</div>
			</div>
		{/if}
	</Dialog.Content>
</Dialog.Root>
