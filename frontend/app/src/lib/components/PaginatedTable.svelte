<script lang="ts" generics="TData">
	import DataTable from '$lib/components/DataTable.svelte';
	import Pagination from '$lib/components/Pagination.svelte';
	import type {
		ColumnDef,
		SortingState,
		VisibilityState,
		FilterFn
	} from '@tanstack/svelte-table';

	let {
		data,
		columns,
		mode = 'client',
		pageSize = 25,
		sorting = $bindable([]),
		columnVisibility = $bindable({}),
		globalFilter = $bindable(''),
		globalFilterFn = undefined,
		onRowClick = undefined,
		// Server mode props
		totalItems = undefined,
		currentPage = $bindable(1),
		onPageChange = undefined,
		onPageSizeChange = undefined
	}: {
		data: TData[];
		columns: ColumnDef<TData, unknown>[];
		mode?: 'client' | 'server';
		pageSize?: number;
		sorting?: SortingState;
		columnVisibility?: VisibilityState;
		globalFilter?: string;
		globalFilterFn?: FilterFn<TData>;
		onRowClick?: (row: TData) => void;
		totalItems?: number;
		currentPage?: number;
		onPageChange?: (page: number) => void;
		onPageSizeChange?: (size: number) => void;
	} = $props();

	// Client mode: internal pagination state
	let clientPage = $state(1);
	let clientPageSizeOverride = $state<number | null>(null);

	const isClient = $derived(mode === 'client');

	const effectiveTotalItems = $derived(isClient ? data.length : (totalItems ?? data.length));
	const effectivePage = $derived(isClient ? clientPage : currentPage);
	const effectivePageSize = $derived(isClient ? (clientPageSizeOverride ?? pageSize) : pageSize);

	// Client mode: slice data for current page
	const displayData = $derived.by(() => {
		if (!isClient) return data;
		const start = (effectivePage - 1) * effectivePageSize;
		return data.slice(start, start + effectivePageSize);
	});

	const showPagination = $derived(effectiveTotalItems > effectivePageSize);

	function handlePageChange(page: number) {
		if (isClient) {
			clientPage = page;
		} else {
			onPageChange?.(page);
		}
	}

	function handlePageSizeChange(size: number) {
		if (isClient) {
			clientPageSizeOverride = size;
			clientPage = 1;
		} else {
			onPageSizeChange?.(size);
		}
	}
</script>

<DataTable
	data={displayData}
	{columns}
	totalItems={effectiveTotalItems}
	pageSize={effectivePageSize}
	bind:sorting
	bind:columnVisibility
	bind:globalFilter
	{globalFilterFn}
	{onRowClick}
/>

{#if showPagination}
	<div class="mt-6">
		<Pagination
			currentPage={effectivePage}
			pageSize={effectivePageSize}
			totalItems={effectiveTotalItems}
			onPageChange={handlePageChange}
			onPageSizeChange={handlePageSizeChange}
		/>
	</div>
{/if}
