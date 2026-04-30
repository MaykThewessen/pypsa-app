import { renderComponent } from '$lib/components/ui/data-table/render-helpers.js';
import { formatDate } from '$lib/utils.js';
import ActionsCell from '$lib/components/cells/ActionsCell.svelte';
import { Trash2 } from 'lucide-svelte';
import type { ColumnDef } from '@tanstack/table-core';
import type { ApiKey } from '$lib/types.js';

interface ApiKeyColumnsHelpers {
	onDelete: (key: ApiKey) => void;
}

export const createColumns = (helpers: ApiKeyColumnsHelpers): ColumnDef<ApiKey, unknown>[] => {
	const { onDelete } = helpers;

	return [
		{
			accessorKey: 'name',
			header: 'Name',
			enableSorting: true,
			sortingFn: 'alphanumeric',
			cell: (info) => {
				return info.getValue() as string;
			}
		},
		{
			accessorKey: 'key_prefix',
			header: 'Prefix',
			enableSorting: false,
			cell: (info) => {
				return `${info.getValue() as string}...`;
			}
		},
		{
			id: 'owner',
			header: 'Bot User',
			enableSorting: true,
			cell: (info) => {
				return info.row.original.owner.username;
			}
		},
		{
			accessorKey: 'created_at',
			header: 'Created',
			enableSorting: true,
			sortingFn: (rowA, rowB) => {
				const a = new Date(rowA.original.created_at).getTime();
				const b = new Date(rowB.original.created_at).getTime();
				return a - b;
			},
			cell: (info) => {
				return formatDate(info.getValue() as string);
			}
		},
		{
			accessorKey: 'last_used_at',
			header: 'Last Used',
			enableSorting: true,
			sortingFn: (rowA, rowB) => {
				const a = rowA.original.last_used_at ? new Date(rowA.original.last_used_at).getTime() : 0;
				const b = rowB.original.last_used_at ? new Date(rowB.original.last_used_at).getTime() : 0;
				return a - b;
			},
			cell: (info) => {
				return formatDate(info.getValue() as string);
			}
		},
		{
			accessorKey: 'expires_at',
			header: 'Expires',
			enableSorting: true,
			sortingFn: (rowA, rowB) => {
				const a = rowA.original.expires_at ? new Date(rowA.original.expires_at).getTime() : 0;
				const b = rowB.original.expires_at ? new Date(rowB.original.expires_at).getTime() : 0;
				return a - b;
			},
			cell: (info) => {
				return formatDate(info.getValue() as string);
			}
		},
		{
			id: 'actions',
			header: '',
			enableSorting: false,
			cell: (info) => {
				const key = info.row.original;
				return renderComponent(ActionsCell, {
					actions: [
						{
							icon: Trash2,
							label: 'Delete',
							onclick: () => onDelete(key),
							variant: 'destructive' as const
						}
					]
				});
			}
		}
	];
};
