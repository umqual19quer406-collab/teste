const AREA_KEY = "ui:area";
const FAVORITES_KEY = "ui:favorites";

const AREA_EVENT = "ui:area-change";
const FAVORITES_EVENT = "ui:favorites-change";

export const AVAILABLE_AREAS = [
  "Area padrao",
  "Comercial",
  "Financeiro",
  "Cadastros",
  "Administracao",
] as const;

export type UiArea = (typeof AVAILABLE_AREAS)[number];

export function getArea(): UiArea {
  const value = localStorage.getItem(AREA_KEY) as UiArea | null;
  return value && AVAILABLE_AREAS.includes(value) ? value : "Area padrao";
}

export function setArea(area: UiArea) {
  localStorage.setItem(AREA_KEY, area);
  window.dispatchEvent(new CustomEvent<UiArea>(AREA_EVENT, { detail: area }));
}

export function onAreaChange(cb: (area: UiArea) => void) {
  const handler = (event: Event) => {
    const custom = event as CustomEvent<UiArea>;
    cb(custom.detail ?? getArea());
  };
  window.addEventListener(AREA_EVENT, handler as EventListener);
  return () => window.removeEventListener(AREA_EVENT, handler as EventListener);
}

export function getFavorites(): string[] {
  try {
    const raw = localStorage.getItem(FAVORITES_KEY);
    const parsed = raw ? JSON.parse(raw) : [];
    return Array.isArray(parsed) ? parsed.filter((item): item is string => typeof item === "string") : [];
  } catch {
    return [];
  }
}

function setFavoritesInternal(favorites: string[]) {
  localStorage.setItem(FAVORITES_KEY, JSON.stringify(favorites));
  window.dispatchEvent(new CustomEvent<string[]>(FAVORITES_EVENT, { detail: favorites }));
}

export function toggleFavorite(path: string) {
  const current = getFavorites();
  if (current.includes(path)) {
    setFavoritesInternal(current.filter((item) => item !== path));
    return;
  }
  setFavoritesInternal([...current, path]);
}

export function onFavoritesChange(cb: (favorites: string[]) => void) {
  const handler = (event: Event) => {
    const custom = event as CustomEvent<string[]>;
    cb(custom.detail ?? getFavorites());
  };
  window.addEventListener(FAVORITES_EVENT, handler as EventListener);
  return () => window.removeEventListener(FAVORITES_EVENT, handler as EventListener);
}
