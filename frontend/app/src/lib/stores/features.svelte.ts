import { version } from '$lib/api/client.js';

export const features = $state({ runsEnabled: false });

export async function initFeatures(): Promise<void> {
	const response = await version.get();
	features.runsEnabled = ((response.snakedispatch_backends as string[]) ?? []).length > 0;
}
