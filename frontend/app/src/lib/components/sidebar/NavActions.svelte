<script>
	import { ScanSearch, Upload } from 'lucide-svelte';
	import {
		SidebarGroup,
		SidebarGroupLabel,
		SidebarMenu,
		SidebarMenuButton,
		SidebarMenuItem
	} from '$lib/components/ui/sidebar';

	// Props for event handlers
	let { onScanNetworks = () => {} } = $props();
</script>

<SidebarGroup>
	<SidebarGroupLabel>Quick Actions</SidebarGroupLabel>
	<SidebarMenu>
		<SidebarMenuItem>
			<SidebarMenuButton on:click={onScanNetworks}>
				<ScanSearch />
				<span>Scan Networks</span>
			</SidebarMenuButton>
		</SidebarMenuItem>
		<SidebarMenuItem>
			<SidebarMenuButton disabled>
				<Upload />
				<span>Upload Network</span>
			</SidebarMenuButton>
		</SidebarMenuItem>
	</SidebarMenu>
</SidebarGroup>
