<script lang="ts">
	import { Pagination as PaginationPrimitive } from "bits-ui";

	import { cn } from "$lib/lib/utils.js";

	let {
		ref = $bindable(null),
		class: className,
		count = 0,
		perPage = 10,
		page = $bindable(1),
		siblingCount = 1,
		child,
		children,
		...restProps
	}: PaginationPrimitive.RootProps = $props();
</script>

<PaginationPrimitive.Root
	bind:ref
	bind:page
	{count}
	{perPage}
	{siblingCount}
	{...restProps}
>
	{#snippet child(snippetProps)}
		<div
			role="navigation"
			aria-label="pagination"
			data-slot="pagination"
			class={cn("mx-auto flex w-full justify-center", className)}
			{...snippetProps.props}
		>
			{@render children?.(snippetProps)}
		</div>
	{/snippet}
</PaginationPrimitive.Root>
