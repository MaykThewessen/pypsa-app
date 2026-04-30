import { renderComponent } from '$lib/components/ui/data-table/render-helpers.js';
import FileCell from '../cells/file-cell.svelte';
import DimensionsCell from '../cells/dimensions-cell.svelte';
import ComponentsCell from '../cells/components-cell.svelte';
import TagsCell from '../cells/tags-cell.svelte';
import UpdateHistoryCell from '../cells/update-history-cell.svelte';
import ActionsCell from '$lib/components/cells/ActionsCell.svelte';
import VisibilityCell from '$lib/components/cells/VisibilityCell.svelte';
import { Lock, Globe, Trash2, UserRoundCog } from 'lucide-svelte';
import OwnerCell from '$lib/components/OwnerCell.svelte';
import type { ColumnDef } from '@tanstack/table-core';
import type { Network, NetworkTag, TagType, TagColor, Visibility } from '$lib/types.js';

interface DatabaseColumnsHelpers {
	getDirectoryPath: (fullPath: string | null | undefined) => string;
	getTagType: (tag: string | NetworkTag) => TagType;
	getTagColor: (type: TagType) => TagColor;
	formatFileSize: (bytes: number | null | undefined) => string;
	formatDate: (dateString: string | null | undefined) => string;
	handleDelete: (id: string) => void;
	toggleComponentsExpanded: (id: string) => void;
	getExpandedComponents: () => Set<string>;
	handleVisibilityToggle: (id: string, visibility: Visibility) => void;
	canEditNetwork: (network: Network) => boolean;
	authEnabled: boolean;
	handleOwnerChange?: (network: Network) => void;
	getDeletingId?: () => string | null;
	getUpdatingVisibilityId?: () => string | null;
}

export const createColumns = (helpers: DatabaseColumnsHelpers): ColumnDef<Network, unknown>[] => {
	const {
		getDirectoryPath,
		getTagType,
		getTagColor,
		formatFileSize,
		formatDate,
		handleDelete,
		toggleComponentsExpanded,
		getExpandedComponents,
		handleVisibilityToggle,
		canEditNetwork,
		authEnabled,
		handleOwnerChange,
		getDeletingId = () => null,
		getUpdatingVisibilityId = () => null
	} = helpers;

	return [
		{
			accessorKey: 'filename',
			header: 'File',
			enableSorting: true,
			sortingFn: 'alphanumeric',
			cell: (info) => {
				const network = info.row.original;
				const dirPath = getDirectoryPath(network.file_path);
				return renderComponent(FileCell, { network, dirPath });
			},
			filterFn: (row, columnId, filterValue) => {
				const network = row.original;
				const searchStr = (filterValue as string).toLowerCase();
				return (
					(network.filename?.toLowerCase().includes(searchStr) ?? false) ||
					(network.name?.toLowerCase().includes(searchStr) ?? false) ||
					(network.file_path?.toLowerCase().includes(searchStr) ?? false)
				);
			}
		},
		{
			accessorKey: 'dimensions_count',
			header: 'Dimensions',
			enableSorting: false,
			cell: (info) => {
				const network = info.row.original;
				return renderComponent(DimensionsCell, { network });
			}
		},
		{
			accessorKey: 'components_count',
			header: 'Components',
			enableSorting: false,
			cell: (info) => {
				const network = info.row.original;
				const isExpanded = getExpandedComponents().has(network.id);
				return renderComponent(ComponentsCell, {
					network,
					isExpanded,
					toggleComponentsExpanded
				});
			}
		},
		{
			accessorKey: 'tags',
			header: 'Tags',
			enableSorting: false,
			cell: (info) => {
				const network = info.row.original;
				return renderComponent(TagsCell, {
					network,
					getTagType,
					getTagColor
				});
			},
			filterFn: (row, columnId, filterValue) => {
				const network = row.original;
				const searchStr = (filterValue as string).toLowerCase();
				if (!network.tags || !Array.isArray(network.tags)) return false;
				return network.tags.some((tag) => {
					if (typeof tag === 'string') {
						return tag.toLowerCase().includes(searchStr);
					} else if (typeof tag === 'object' && tag.name) {
						return tag.name.toLowerCase().includes(searchStr);
					}
					return false;
				});
			}
		},
		// Auth-only columns
		...(authEnabled
			? [
					{
						accessorKey: 'visibility',
						header: 'Visibility',
						enableSorting: true,
						cell: (info: { row: { original: Network } }) => {
							const network = info.row.original;
							return renderComponent(VisibilityCell, {
								item: network,
								canEdit: canEditNetwork(network),
								onToggle: handleVisibilityToggle
							});
						}
					},
					{
						accessorKey: 'owner',
						header: 'Owner',
						enableSorting: false,
						cell: (info: { row: { original: Network } }) => {
							const network = info.row.original;
							return renderComponent(OwnerCell, { item: network });
						}
					}
				] as ColumnDef<Network, unknown>[]
			: []),
		{
			accessorKey: 'file_size',
			header: 'Size',
			enableSorting: true,
			sortingFn: 'basic',
			cell: (info) => {
				return formatFileSize(info.getValue() as number);
			}
		},
		{
			accessorKey: 'update_history',
			header: 'Last Updated',
			enableSorting: true,
			sortingFn: (rowA, rowB) => {
				const historyA = rowA.original.update_history;
				const historyB = rowB.original.update_history;

				// Get the most recent update for each row
				const latestA = historyA && historyA.length > 0
					? new Date(historyA[historyA.length - 1]).getTime()
					: 0;
				const latestB = historyB && historyB.length > 0
					? new Date(historyB[historyB.length - 1]).getTime()
					: 0;

				return latestA - latestB;
			},
			cell: (info) => {
				const network = info.row.original;
				return renderComponent(UpdateHistoryCell, { network, formatDate });
			}
		},
		{
			id: 'actions',
			header: 'Actions',
			enableSorting: false,
			cell: (info) => {
				const network = info.row.original;
				const canEdit = canEditNetwork(network);
				const isPublic = network.visibility === 'public';
				const isDeleting = getDeletingId() === network.id;
				const isUpdatingVisibility = getUpdatingVisibilityId() === network.id;
				const actions = [];
				if (canEdit) {
					if (handleOwnerChange) {
						actions.push({
							icon: UserRoundCog,
							label: 'Change owner',
							onclick: () => handleOwnerChange(network)
						});
					}
					actions.push({
						icon: isPublic ? Lock : Globe,
						label: isPublic ? 'Make private' : 'Make public',
						onclick: () => handleVisibilityToggle(network.id, isPublic ? 'private' : 'public'),
						loading: isUpdatingVisibility,
						loadingLabel: 'Updating...'
					});
					actions.push({
						icon: Trash2,
						label: 'Delete',
						onclick: () => handleDelete(network.id),
						loading: isDeleting,
						loadingLabel: 'Deleting...',
						variant: 'destructive' as const
					});
				}
				return renderComponent(ActionsCell, { actions });
			}
		}
	] as ColumnDef<Network, unknown>[];
};
