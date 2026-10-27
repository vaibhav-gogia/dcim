import { useAuth } from "../AuthContext";
import { useState } from "react";
import { ReactNode } from "react";
import { Link } from "react-router-dom";

import { colors, fontSize, radius, space } from "../theme";
import { useTheme } from "../ThemeContext";

export interface Crumb {
  label: string;
  to?: string;
}

function ThemeToggle() {
  const { theme, toggleTheme } = useTheme();
  return (
    <button
      onClick={toggleTheme}
      title={theme === "dark" ? "Switch to light mode" : "Switch to dark mode"}
      style={{
        width: 36,
        height: 36,
        display: "flex",
        alignItems: "center",
        justifyContent: "center",
        border: `1px solid ${colors.border}`,
        borderRadius: radius.sm,
        background: colors.surface2,
        color: colors.textPrimary,
        cursor: "pointer",
        fontSize: fontSize.md,
      }}
    >
      {theme === "dark" ? "☀" : "☾"}
    </button>
  );
}

export default function PageShell({ crumbs, title, actions, children }: { crumbs: Crumb[]; title: string; actions?: ReactNode; children: ReactNode }) {
  const auth = useAuth();
  const [logoutError, setLogoutError] = useState<string | null>(null);
  const navigationCrumbs = crumbs.filter(crumb => crumb.label !== "DCIM");
  return (
    <div style={{ minHeight: "100vh" }}>
      <header style={{
        padding: `${space.sm}px ${space.xl}px`,
        borderBottom: `1px solid ${colors.border}`,
        background: colors.surface0,
        display: "flex",
        flexWrap: "wrap",
        gap: space.lg,
        alignItems: "center",
        justifyContent: "space-between",
      }}>
        <nav aria-label="Breadcrumb" style={{ display: "flex", alignItems: "center", gap: space.md, minWidth: 0 }}>
          <Link to="/" aria-label="DCIM home" style={{ display: "inline-flex", alignItems: "center", gap: space.sm, color: colors.textPrimary, textDecoration: "none", flexShrink: 0 }}>
            <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" aria-hidden="true">
              <rect x="4" y="3" width="16" height="18" rx="3" />
              <path d="M4 9h16M4 15h16M8 6h2M8 12h2M8 18h2" />
            </svg>
            <span style={{ fontSize: fontSize.sm, fontWeight: 650, letterSpacing: "0.08em" }}>DCIM</span>
          </Link>
          {navigationCrumbs.length > 0 && <ol style={{ display: "flex", flexWrap: "wrap", alignItems: "center", gap: space.sm, listStyle: "none", margin: 0, padding: 0, fontSize: fontSize.sm }}>
            {navigationCrumbs.map((crumb, i) => <li key={i} style={{ display: "flex", alignItems: "center", gap: space.sm }}>
              <span aria-hidden="true" style={{ color: colors.textMuted }}>/</span>
              {crumb.to ? <Link to={crumb.to} style={{ color: colors.textMuted, textDecoration: "none" }}>{crumb.label}</Link>
                : <span aria-current="page" style={{ color: colors.textSecondary }}>{crumb.label}</span>}
            </li>)}
          </ol>}
        </nav>
        <div style={{ display: "flex", flexWrap: "wrap", alignItems: "center", gap: space.md }}>
          <Link to="/inventory" style={{ display: "inline-flex", alignItems: "center", gap: space.xs, color: colors.textSecondary, fontSize: fontSize.sm, textDecoration: "none" }}>
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" aria-hidden="true" style={{ flexShrink: 0 }}>
              <circle cx="10.5" cy="10.5" r="6.5" />
              <path d="m16 16 4.5 4.5" />
            </svg>
            Search inventory
          </Link>
          <Link to="/history" style={{ color: colors.textSecondary, fontSize: fontSize.sm }}>Activity</Link>
          <Link to="/account" style={{ color: colors.textSecondary, fontSize: fontSize.sm }}>{auth.user?.username} · {auth.user?.role}</Link>
          <button onClick={async () => { try { await auth.logout(); } catch (e) { setLogoutError(e instanceof Error ? e.message : "Sign-out failed"); } }} style={{ padding: space.sm, background: colors.surface2, color: colors.textPrimary, border: `1px solid ${colors.border}`, borderRadius: radius.sm }}>Sign out</button>
          <ThemeToggle />
        </div>
      </header>
      <main style={{ padding: space.xl }}>
        {logoutError && <p role="alert">{logoutError}</p>}
        <div style={{ display: "flex", flexWrap: "wrap", alignItems: "center", justifyContent: "space-between", gap: space.md, marginBottom: space.lg }}>
          <h1 style={{ margin: 0, fontSize: fontSize.xl, fontWeight: 600, letterSpacing: "-0.025em", color: colors.textPrimary }}>{title}</h1>
          {actions && <div style={{ display: "flex", flexWrap: "wrap", alignItems: "center", gap: space.sm }}>{actions}</div>}
        </div>
        {children}
      </main>
    </div>
  );
}
