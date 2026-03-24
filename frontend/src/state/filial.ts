const KEY = "filial";

export function getFilial(): string {
  return localStorage.getItem(KEY) ?? "01";
}

export function setFilial(filial: string) {
  localStorage.setItem(KEY, filial);
  // notifica telas abertas
  window.dispatchEvent(new CustomEvent("filial:change", { detail: filial }));
}

export function onFilialChange(cb: (filial: string) => void) {
  const handler = (e: Event) => {
    const custom = e as CustomEvent<string>;
    cb(custom.detail ?? getFilial());
  };
  window.addEventListener("filial:change", handler as EventListener);
  return () => window.removeEventListener("filial:change", handler as EventListener);
}
