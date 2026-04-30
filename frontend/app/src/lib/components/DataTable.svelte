<script lang="ts" generics="TData">
	import {
		createTable,
		getCoreRowModel,
		getSortedRowModel,
		getFilteredRowModel,
		type ColumnDef,
		type SortingState,
		type VisibilityState,
		type Updater,
		type FilterFn
	} from '@tanstack/svelte-table';
	import * as Table from '$lib/components/ui/table';
	import FlexRender from '$lib/components/ui/data-table/flex-render.svelte';
	import { ArrowUpDown, ArrowUp, ArrowDown } from 'lucide-svelte';

	let {
		data,
		columns,
		totalItems,
		pageSize,
		sorting = $bindable([]),
		columnVisibility = $bindable({}),
		globalFilter = $bindable(''),
		globalFilterFn = undefined,
		onRowClick = undefined
	}: {
		data: TData[];
		columns: ColumnDef<TData, unknown>[];
		totalItems: number;
		pageSize: number;
		sorting?: SortingState;
		columnVisibility?: VisibilityState;
		globalFilter?: string;
		globalFilterFn?: FilterFn<TData>;
		onRowClick?: (row: TData) => void;
	} = $props();

	const table = createTable<TData>({
		get data() {
			return data;
		},
		get columns() {
			return columns;
		},
		getCoreRowModel: getCoreRowModel(),
		getSortedRowModel: getSortedRowModel(),
		getFilteredRowModel: getFilteredRowModel(),
		manualPagination: true,
		get pageCount() {
			return Math.ceil(totalItems / pageSize);
		},
		state: {
			get sorting() {
				return sorting;
			},
			get columnVisibility() {
				return columnVisibility;
			},
			get globalFilter() {
				return globalFilter;
			}
		},
		onSortingChange: (updater: Updater<SortingState>) => {
			sorting = typeof updater === 'function' ? updater(sorting) : updater;
		},
		onColumnVisibilityChange: (updater: Updater<VisibilityState>) => {
			columnVisibility = typeof updater === 'function' ? updater(columnVisibility) : updater;
		},
		onGlobalFilterChange: (updater: Updater<string>) => {
			globalFilter = typeof updater === 'function' ? updater(globalFilter) : updater;
		},
		get globalFilterFn() {
			return globalFilterFn ?? (() => true);
		}
	});
</script>

<div class="bg-card rounded-lg border border-border overflow-hidden">
	<div class="overflow-x-auto">
		<Table.Root>
			<Table.Header>
				{#each table.getHeaderGroups() as headerGroup}
					<Table.Row>
						{#each headerGroup.headers as header}
							<Table.Head>
								{#if !header.isPlaceholder}
									{#if header.column.getCanSort()}
										<button
											class="flex items-center gap-2 hover:text-foreground transition-colors"
											onclick={header.column.getToggleSortingHandler()}
										>
											<!-- eslint-disable-next-line @typescript-eslint/no-explicit-any -->
										<FlexRender
												content={header.column.columnDef.header as any}
												context={header.getContext() as any}
											/>
											{#if header.column.getIsSorted() === 'asc'}
												<ArrowUp class="h-4 w-4" />
											{:else if header.column.getIsSorted() === 'desc'}
												<ArrowDown class="h-4 w-4" />
											{:else}
												<ArrowUpDown class="h-4 w-4 opacity-50" />
											{/if}
										</button>
									{:else}
										<!-- eslint-disable-next-line @typescript-eslint/no-explicit-any -->
										<FlexRender
											content={header.column.columnDef.header as any}
											context={header.getContext() as any}
										/>
									{/if}
								{/if}
							</Table.Head>
						{/each}
					</Table.Row>
				{/each}
			</Table.Header>
			<Table.Body>
				{#each table.getRowModel().rows as row}
					<Table.Row
						class="hover:bg-muted/30 transition-colors cursor-pointer"
						onclick={() => onRowClick?.(row.original)}
					>
						{#each row.getVisibleCells() as cell}
							<Table.Cell>
								<!-- eslint-disable-next-line @typescript-eslint/no-explicit-any -->
								<FlexRender
									content={cell.column.columnDef.cell as any}
									context={cell.getContext() as any}
								/>
							</Table.Cell>
						{/each}
					</Table.Row>
				{/each}
			</Table.Body>
		</Table.Root>
	</div>
</div>
