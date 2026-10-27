import { createContext, ReactNode, useContext, useEffect, useState } from "react";
import { useQueryClient } from "@tanstack/react-query";
import { api, ApiError } from "./api/client";

export interface User { id: string; username: string; role: "viewer" | "operator" | "admin"; is_active: boolean }
interface Auth { user: User | null; loading: boolean; error: string | null; reload: () => Promise<void>; login: (username: string, password: string) => Promise<void>; logout: () => Promise<void> }
const Context = createContext<Auth | null>(null);
export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<User | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const client = useQueryClient();
  async function reload() {
    setLoading(true); setError(null);
    try { setUser(await api.get<User>("/auth/me")); }
    catch (e) { if (!(e instanceof ApiError && e.status === 401)) setError(e instanceof Error ? e.message : "Unable to connect"); setUser(null); }
    finally { setLoading(false); }
  }
  useEffect(() => {
    void reload();
    const expired = () => { setUser(null); client.clear(); };
    window.addEventListener("auth-expired", expired);
    return () => window.removeEventListener("auth-expired", expired);
  }, []);
  async function login(username: string, password: string) { const next = await api.post<User>("/auth/login", { username, password }); client.clear(); setUser(next); setError(null); }
  async function logout() { await api.post("/auth/logout"); client.clear(); setUser(null); }
  return <Context.Provider value={{ user, loading, error, reload, login, logout }}>{children}</Context.Provider>;
}
export function useAuth() { const auth = useContext(Context); if (!auth) throw new Error("AuthProvider required"); return auth; }
export function AdminOnly({ children }: { children: ReactNode }) { return useAuth().user?.role === "admin" ? <>{children}</> : null; }
export function usePermissions() { const { user } = useAuth(); return { canManage: user?.role === "admin", canOperate: user?.role === "admin" || user?.role === "operator" }; }
