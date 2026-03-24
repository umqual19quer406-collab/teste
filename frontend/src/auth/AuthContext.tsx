import React, { createContext, useContext, useEffect, useMemo, useState } from "react";
import { login as apiLogin, type LoginResponse } from "../api/auth";

type AuthState = {
  token: string | null;
  isAuthenticated: boolean;
  login: (u: string, p: string) => Promise<void>;
  logout: () => void;
};

const Ctx = createContext<AuthState | null>(null);

function getToken() {
  return localStorage.getItem("token");
}

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const [token, setToken] = useState<string | null>(() => getToken());

  // ✅ sincroniza token entre abas/janelas
  useEffect(() => {
    const onStorage = (e: StorageEvent) => {
      if (e.key === "token") setToken(getToken());
    };
    window.addEventListener("storage", onStorage);
    return () => window.removeEventListener("storage", onStorage);
  }, []);

  const value = useMemo<AuthState>(
    () => ({
      token,
      isAuthenticated: !!token,

      login: async (u, p) => {
        const r: LoginResponse = await apiLogin(u, p);
        localStorage.setItem("token", r.access_token);
        setToken(r.access_token);
      },

      logout: () => {
        localStorage.removeItem("token");
        setToken(null);
        // ✅ UX: manda pro login
        if (window.location.pathname !== "/login") window.location.assign("/login");
      },
    }),
    [token]
  );

  return <Ctx.Provider value={value}>{children}</Ctx.Provider>;
}

// eslint-disable-next-line react-refresh/only-export-components
export function useAuth() {
  const v = useContext(Ctx);
  if (!v) throw new Error("useAuth must be used within AuthProvider");
  return v;
}
