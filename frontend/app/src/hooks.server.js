/**
 * SvelteKit server hooks for API proxying
 * This ensures API requests work during SSR and client-side navigation
 */

const API_BASE_URL = 'http://localhost:8000';

/** @type {import('@sveltejs/kit').Handle} */
export async function handle({ event, resolve }) {
	// Proxy /api requests to the backend
	if (event.url.pathname.startsWith('/api')) {
		const targetUrl = `${API_BASE_URL}${event.url.pathname}${event.url.search}`;

		try {
			const response = await fetch(targetUrl, {
				method: event.request.method,
				headers: event.request.headers,
				body: event.request.method !== 'GET' && event.request.method !== 'HEAD'
					? await event.request.text()
					: undefined
			});

			// Create a new response with the proxied content
			const responseBody = await response.text();

			return new Response(responseBody, {
				status: response.status,
				statusText: response.statusText,
				headers: {
					'content-type': response.headers.get('content-type') || 'application/json',
					'cache-control': response.headers.get('cache-control') || 'no-cache'
				}
			});
		} catch (error) {
			console.error('API proxy error:', error);
			return new Response(
				JSON.stringify({
					detail: `Failed to connect to backend: ${error.message}`
				}),
				{
					status: 502,
					headers: { 'content-type': 'application/json' }
				}
			);
		}
	}

	// For non-API requests, proceed as normal
	return resolve(event);
}
