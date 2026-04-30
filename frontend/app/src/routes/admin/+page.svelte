<script lang="ts">
	import { Plus } from 'lucide-svelte';
	import { Button } from '$lib/components/ui/button';
	import * as Tabs from '$lib/components/ui/tabs';
	import AdminUsers from './components/AdminUsers.svelte';
	import AdminApiKeys from './components/AdminApiKeys.svelte';
	import AdminBackends from './components/AdminBackends.svelte';

	let activeTab = $state('users');
	let createUserOpen = $state(false);
	let createKeyOpen = $state(false);

	const tabTitles: Record<string, string> = {
		users: 'Users',
		'api-keys': 'API Keys',
		backends: 'Backends'
	};
</script>

<svelte:head>
	<title>Admin - {tabTitles[activeTab] ?? 'Administration'} - PyPSA App</title>
</svelte:head>

<div class="min-h-screen">
	<div class="max-w-[80rem] mx-auto py-8">
		<Tabs.Root bind:value={activeTab}>
			<div class="flex items-center gap-2 mb-2">
				<Tabs.List>
					<Tabs.Trigger value="users">Users</Tabs.Trigger>
					<Tabs.Trigger value="api-keys">API Keys</Tabs.Trigger>
					<Tabs.Trigger value="backends">Backends</Tabs.Trigger>
				</Tabs.List>
				<div class="flex-1"></div>
				{#if activeTab === 'users'}
					<Button size="sm" onclick={() => (createUserOpen = true)}>
						<Plus class="mr-1 size-4" />
						Create User
					</Button>
				{:else if activeTab === 'api-keys'}
					<Button size="sm" onclick={() => (createKeyOpen = true)}>
						<Plus class="mr-1 size-4" />
						Create API Key
					</Button>
				{/if}
			</div>
			<Tabs.Content value="users">
				<AdminUsers bind:createOpen={createUserOpen} />
			</Tabs.Content>
			<Tabs.Content value="api-keys">
				<AdminApiKeys bind:createOpen={createKeyOpen} />
			</Tabs.Content>
			<Tabs.Content value="backends">
				<AdminBackends />
			</Tabs.Content>
		</Tabs.Root>
	</div>
</div>
