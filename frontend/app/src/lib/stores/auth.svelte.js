/**
 * Authentication store using Svelte 5 runes
 * Manages user session state and provides auth methods
 */

import { auth } from '$lib/api/client.js';

class AuthStore {
	user = $state(null);
	loading = $state(true);
	error = $state(null);

	/**
	 * Initialize auth state by fetching current user
	 * Call this on app startup
	 */
	async init() {
		this.loading = true;
		this.error = null;

		try {
			const response = await auth.me();
			this.user = response;
		} catch (err) {
			// Not logged in or auth is disabled
			this.user = null;
			// Don't set error for 401/400, these are expected when not logged in
			if (err.status && (err.status === 401 || err.status === 400)) {
				this.error = null;
			} else {
				console.error('Failed to fetch user:', err);
				this.error = err.message;
			}
		} finally {
			this.loading = false;
		}
	}

	/**
	 * Redirect to GitHub OAuth login
	 */
	login() {
		auth.login();
	}

	/**
	 * Logout and clear session
	 */
	async logout() {
		this.loading = true;
		try {
			// Call logout endpoint (will redirect to login page)
			auth.logout();
		} catch (err) {
			console.error('Logout failed:', err);
			this.error = err.message;
			this.loading = false;
		}
	}

	/**
	 * Check if user is authenticated
	 */
	get isAuthenticated() {
		return this.user !== null;
	}

	/**
	 * Get user's display name
	 */
	get displayName() {
		return this.user?.username || 'User';
	}

	/**
	 * Get user's avatar URL
	 */
	get avatarUrl() {
		return this.user?.avatar_url || null;
	}
}

export const authStore = new AuthStore();
