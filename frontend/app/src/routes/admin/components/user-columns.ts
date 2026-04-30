import { renderComponent } from '$lib/components/ui/data-table/render-helpers.js';
import { formatDate } from '$lib/utils.js';
import UserCell from '$lib/components/cells/UserCell.svelte';
import BadgeCell from '$lib/components/cells/BadgeCell.svelte';
import ActionsCell from '$lib/components/cells/ActionsCell.svelte';
import { Check, Settings } from 'lucide-svelte';
import type { ColumnDef } from '@tanstack/table-core';
import type { User } from '$lib/types.js';

interface UserColumnsHelpers {
	onApprove: (userId: string) => void;
	onOpenPermissions: (user: User) => void;
}

function getRoleBadgeVariant(role: string) {
	if (role === 'admin') return 'default' as const;
	if (role === 'bot' || role === 'user') return 'secondary' as const;
	return 'outline' as const;
}

export const createColumns = (helpers: UserColumnsHelpers): ColumnDef<User, unknown>[] => {
	const { onApprove, onOpenPermissions } = helpers;

	return [
		{
			accessorKey: 'username',
			header: 'User',
			enableSorting: true,
			sortingFn: 'alphanumeric',
			cell: (info) => {
				return renderComponent(UserCell, { user: info.row.original });
			}
		},
		{
			accessorKey: 'email',
			header: 'Email',
			enableSorting: true,
			sortingFn: 'alphanumeric',
			cell: (info) => {
				return (info.getValue() as string) || '\u2014';
			}
		},
		{
			accessorKey: 'role',
			header: 'Role',
			enableSorting: true,
			cell: (info) => {
				const role = info.getValue() as string;
				return renderComponent(BadgeCell, {
					label: role,
					variant: getRoleBadgeVariant(role)
				});
			}
		},
		{
			accessorKey: 'created_at',
			header: 'Created',
			enableSorting: true,
			sortingFn: (rowA, rowB) => {
				const a = rowA.original.created_at ? new Date(rowA.original.created_at).getTime() : 0;
				const b = rowB.original.created_at ? new Date(rowB.original.created_at).getTime() : 0;
				return a - b;
			},
			cell: (info) => {
				return formatDate(info.getValue() as string);
			}
		},
		{
			accessorKey: 'last_login',
			header: 'Last Login',
			enableSorting: true,
			sortingFn: (rowA, rowB) => {
				const a = rowA.original.last_login ? new Date(rowA.original.last_login).getTime() : 0;
				const b = rowB.original.last_login ? new Date(rowB.original.last_login).getTime() : 0;
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
				const user = info.row.original;
				const actions = [];
				if (user.role === 'pending') {
					actions.push({
						icon: Check,
						label: 'Approve',
						onclick: () => onApprove(user.id)
					});
				}
				actions.push({
					icon: Settings,
					label: 'Permissions',
					onclick: () => onOpenPermissions(user)
				});
				return renderComponent(ActionsCell, { actions });
			}
		}
	];
};
