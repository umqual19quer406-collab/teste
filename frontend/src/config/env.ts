function readRequiredEnv(name: string): string {
  const value = import.meta.env[name as keyof ImportMetaEnv];

  if (typeof value !== "string" || !value.trim()) {
    throw new Error(`Variavel obrigatoria ausente: ${name}. Configure frontend/.env antes de iniciar o app.`);
  }

  return value.trim().replace(/\/+$/, "");
}

export const API_BASE_URL = readRequiredEnv("VITE_API_BASE_URL");
