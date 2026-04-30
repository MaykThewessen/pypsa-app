import { writable, derived } from "svelte/store";
import type { Network, Carrier } from "$lib/types.js";

// Network selection state
export const selectedNetworkIds = writable<Set<string>>(new Set());
export const compareMode = writable<boolean>(false);
export const networksList = writable<Network[]>([]);
export const loadingNetworks = writable<boolean>(true);

// Filter state
export const selectedCarriers = writable<Set<string>>(new Set());
export const selectedCountries = writable<Set<string>>(new Set());
export const showIndividualPlots = writable<boolean>(true);
export const filtersPanelCollapsed = writable<boolean>(false);

// Available options (populated from network data)
export const availableCarriers = writable<Carrier[]>([]);
export const availableCountries = writable<string[]>([]);

// Derived state
export const selectedNetworks = derived(
  [networksList, selectedNetworkIds],
  ([$networksList, $selectedNetworkIds]) => {
    return $networksList.filter((network) =>
      $selectedNetworkIds.has(network.id),
    );
  },
);

export const hasSelection = derived(
  selectedNetworkIds,
  ($ids) => $ids.size > 0,
);

// Actions
export function toggleNetwork(networkId: string): void {
  selectedNetworkIds.update((ids) => {
    const newIds = new Set(ids);
    if (newIds.has(networkId)) {
      newIds.delete(networkId);
    } else {
      newIds.add(networkId);
    }
    return newIds;
  });
}

export function selectNetwork(networkId: string): void {
  selectedNetworkIds.set(new Set([networkId]));
}

export function clearSelection(): void {
  selectedNetworkIds.set(new Set());
}

export function toggleCompareMode(): void {
  compareMode.update((v) => !v);
}

export function setCompareMode(value: boolean): void {
  compareMode.set(value);
}

export function toggleCarrier(carrier: string): void {
  selectedCarriers.update((carriers) => {
    const newCarriers = new Set(carriers);
    if (newCarriers.has(carrier)) {
      newCarriers.delete(carrier);
    } else {
      newCarriers.add(carrier);
    }
    return newCarriers;
  });
}

export function toggleCountry(country: string): void {
  selectedCountries.update((countries) => {
    const newCountries = new Set(countries);
    if (newCountries.has(country)) {
      newCountries.delete(country);
    } else {
      newCountries.add(country);
    }
    return newCountries;
  });
}

export function resetFilters(): void {
  selectedCarriers.set(new Set());
  selectedCountries.set(new Set());
  showIndividualPlots.set(true);
}

export function resetAll(): void {
  clearSelection();
  resetFilters();
  compareMode.set(false);
}
