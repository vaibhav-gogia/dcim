import { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { useAuth } from "../AuthContext";
import { api } from "../api/client";
import { colors, radius, space } from "../theme";

export default function LoginPage() {
  const { login } = useAuth();
  const setup = useQuery({ queryKey: ["setup-status"], queryFn: () => api.get<{ needs_setup: boolean }>("/auth/setup-status"), retry: false });
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [showPassword, setShowPassword] = useState(false);
  const [pending, setPending] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const input = { padding: space.sm, background: colors.surface0, color: colors.textPrimary, border: `1px solid ${colors.border}`, borderRadius: radius.sm, fontSize: 16 };
  return <main style={{ minHeight: "100vh", display: "grid", placeItems: "center", padding: space.lg }}>
    <section style={{ width: "100%", maxWidth: 460, padding: space.xl, background: colors.surface1, border: `1px solid ${colors.border}`, borderRadius: radius.md }}>
      <h1 style={{ marginTop: 0 }}>Sign in to DCIM</h1>
      {setup.data?.needs_setup && <><p>Create the first administrator from your project terminal:</p><code style={{ display: "block", overflowWrap: "anywhere" }}>docker compose exec backend python -m app.bootstrap_admin</code><p>Then sign in below. There are no default credentials.</p></>}
      {setup.error && <p role="alert">Unable to check account setup. Verify the backend and migrations.</p>}
      <form onSubmit={async e => { e.preventDefault(); setPending(true); setShowPassword(false); setError(null); try { await login(username.trim().toLowerCase(), password); } catch (reason) { setError(reason instanceof Error ? reason.message : "Sign-in failed"); } finally { setPending(false); setPassword(""); } }}>
        <fieldset disabled={pending} style={{ border: 0, padding: 0, display: "grid", gap: space.md }}>
          <label style={{ display: "grid", gap: space.xs }}>Username<input autoFocus autoComplete="username" required maxLength={64} style={input} value={username} onChange={e => setUsername(e.target.value)} /></label>
          <div style={{ display: "grid", gap: space.xs }}>
            <label htmlFor="login-password">Password</label>
            <div style={{ display: "flex", gap: space.xs }}>
              <input id="login-password" type={showPassword ? "text" : "password"} autoComplete="current-password" required maxLength={128} style={{ ...input, flex: 1, minWidth: 0 }} value={password} onChange={e => setPassword(e.target.value)} />
              <button type="button" aria-controls="login-password" aria-pressed={showPassword} onClick={() => setShowPassword(visible => !visible)} style={{ ...input, cursor: "pointer" }}>
                {showPassword ? "Hide password" : "Show password"}
              </button>
            </div>
          </div>
          {error && <p role="alert" style={{ color: colors.statusCritical }}>{error}</p>}
          <button style={{ ...input, cursor: "pointer" }} type="submit">{pending ? "Signing in…" : "Sign in"}</button>
        </fieldset>
      </form>
    </section>
  </main>;
}
