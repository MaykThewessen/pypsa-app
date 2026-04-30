<script lang="ts">
	import { page } from '$app/stores';
	import { Shield } from 'lucide-svelte';
	import { authStore } from '$lib/stores/auth.svelte.js';
	import * as Sidebar from '$lib/components/ui/sidebar';

	const currentPath = $derived($page.url.pathname);
</script>

{#if authStore.isAdmin}
	<Sidebar.Group>
		<Sidebar.GroupLabel>Administration</Sidebar.GroupLabel>
		<Sidebar.GroupContent>
			<Sidebar.Menu>
				<Sidebar.MenuItem>
					<Sidebar.MenuButton
						tooltipContent="Administration"
						isActive={currentPath.startsWith('/admin')}
					>
						{#snippet child({ props }: { props: Record<string, unknown> })}
							<a href="/admin" {...props}>
								<Shield />
								<span>Administration</span>
							</a>
						{/snippet}
					</Sidebar.MenuButton>
				</Sidebar.MenuItem>
			</Sidebar.Menu>
		</Sidebar.GroupContent>
	</Sidebar.Group>
{/if}
