import { auth } from '$lib/api/client.js';
import type { User, ApiError, Permission } from '$lib/types.js';

class AuthStore {
	user: User | null = $state(null);
	loading: boolean = $state(true);
	error: string | null = $state(null);
	authEnabled: boolean | null = $state(null);

	async init(): Promise<void> {
		this.loading = true;
		this.error = null;

		try {
			const response = await auth.me();
			this.user = response;
			this.authEnabled = true;
		} catch (err) {
			const apiErr = err as ApiError;
			if (apiErr.status === 400) {
				this.authEnabled = false;
				this.user = null;
				this.error = null;
			} else if (apiErr.status === 401) {
				this.authEnabled = true;
				this.user = null;
				this.error = null;
			} else {
				console.error('Failed to fetch user:', err);
				this.error = apiErr.message;
			}
		} finally {
			this.loading = false;
		}
	}

	login(): void {
		auth.login();
	}

	async logout(): Promise<void> {
		this.loading = true;
		try {
			auth.logout();
		} catch (err) {
			console.error('Logout failed:', err);
			this.error = (err as Error).message;
			this.loading = false;
		}
	}

	get isAuthenticated(): boolean {
		return this.user !== null;
	}

	get displayName(): string {
		return this.user?.username || 'User';
	}

	get avatarUrl(): string | null {
		return this.user?.avatar_url || null;
	}

	get permissions(): string[] {
		return this.user?.permissions || [];
	}

	hasPermission(permission: Permission): boolean {
		return this.permissions.includes(permission);
	}

	get isAdmin(): boolean {
		return this.hasPermission('users:manage');
	}

	get isApproved(): boolean {
		return this.permissions.length > 0;
	}

	get isPending(): boolean {
		return this.isAuthenticated && !this.isApproved;
	}
}

export const authStore = new AuthStore();
