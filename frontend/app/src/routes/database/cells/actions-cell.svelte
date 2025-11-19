<script>
	import { Button } from '$lib/components/ui/button';
	import * as DropdownMenu from '$lib/components/ui/dropdown-menu';
	import { MoreVertical, Trash2 } from 'lucide-svelte';

	let { network, handleDelete } = $props();
</script>

<div onclick={(e) => e.stopPropagation()} onkeydown={(e) => e.key === 'Enter' && e.stopPropagation()} role="button" tabindex="-1">
	<DropdownMenu.Root>
		<DropdownMenu.Trigger asChild>
			{#snippet child({ props })}
				<Button variant="ghost" size="sm" {...props} class="h-8 w-8 p-0">
					<MoreVertical class="h-4 w-4" />
					<span class="sr-only">Open menu</span>
				</Button>
			{/snippet}
		</DropdownMenu.Trigger>
		<DropdownMenu.Content align="end">
			<DropdownMenu.Item
				onclick={() => handleDelete(network.id)}
				class="text-destructive focus:text-destructive"
			>
				<Trash2 class="h-4 w-4 mr-2" />
				Delete
			</DropdownMenu.Item>
		</DropdownMenu.Content>
	</DropdownMenu.Root>
</div>
