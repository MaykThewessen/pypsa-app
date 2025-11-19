<script>
	import { page } from '$app/stores';
	import { Home, Database, Network } from 'lucide-svelte';
	import * as Sidebar from '$lib/components/ui/sidebar';

	const navItems = [
		{
			title: 'Home',
			url: '/',
			icon: Home
		},
		{
			title: 'Database',
			url: '/database',
			icon: Database
		},
		{
			title: 'Network',
			url: '/network',
			icon: Network
		}
	];

	// Reactive variable to check current path
	const currentPath = $derived($page.url.pathname);
</script>

<Sidebar.Group>
	<Sidebar.GroupLabel>Navigation</Sidebar.GroupLabel>
	<Sidebar.GroupContent>
		<Sidebar.Menu>
			{#each navItems as item}
				<Sidebar.MenuItem>
					<Sidebar.MenuButton tooltipContent={item.title} isActive={currentPath === item.url}>
						{#snippet child({ props })}
							<a href={item.url} {...props}>
								<item.icon />
								<span>{item.title}</span>
							</a>
						{/snippet}
					</Sidebar.MenuButton>
				</Sidebar.MenuItem>
			{/each}
		</Sidebar.Menu>
	</Sidebar.GroupContent>
</Sidebar.Group>
