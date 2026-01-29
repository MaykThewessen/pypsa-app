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
	let { onScanNetworks = () => {}, onUploadNetwork = () => {} } = $props();

	let fileInput: HTMLInputElement;

	function handleUploadClick() {
		fileInput?.click();
	}

	async function handleFileSelect(event: Event) {
		const input = event.target as HTMLInputElement;
		const file = input.files?.[0];
		if (!file) return;

		// Validate file extension
		if (!file.name.endsWith('.nc')) {
			alert('Only NetCDF (.nc) files are supported');
			return;
		}

		const formData = new FormData();
		formData.append('file', file);

		try {
			const response = await fetch('/api/networks/upload', {
				method: 'POST',
				body: formData
			});

			if (!response.ok) {
				const error = await response.json();
				alert(error.detail || 'Upload failed');
				return;
			}

			const result = await response.json();
			alert(result.message);
			onUploadNetwork();
		} catch (error) {
			alert('Upload failed: ' + error);
		}

		// Reset file input
		input.value = '';
	}
</script>

<input
	type="file"
	accept=".nc"
	bind:this={fileInput}
	on:change={handleFileSelect}
	style="display: none;"
/>

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
			<SidebarMenuButton on:click={handleUploadClick}>
				<Upload />
				<span>Upload Network</span>
			</SidebarMenuButton>
		</SidebarMenuItem>
	</SidebarMenu>
</SidebarGroup>
