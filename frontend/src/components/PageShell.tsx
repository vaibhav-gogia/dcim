import { useAuth } from "../AuthContext";
import { useEffect, useId, useRef, useState, ReactNode } from "react";
import { Link, NavLink } from "react-router-dom";

import { colors, fontSize, space } from "../theme";
import { useTheme } from "../ThemeContext";

export interface Crumb {
  label: string;
  to?: string;
}

function Icon({ children }: { children: ReactNode }) {
  return <svg width="17" height="17" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.7" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true" style={{ flexShrink: 0 }}>{children}</svg>;
}

function ThemeToggle() {
  const { theme, toggleTheme } = useTheme();
  const label = theme === "dark" ? "Switch to light mode" : "Switch to dark mode";
  return <button className="header-control header-icon-button" onClick={toggleTheme} title={label} aria-label={label}>
    {theme === "dark" ? <Icon><circle cx="12" cy="12" r="4" /><path d="M12 2v2m0 16v2M2 12h2m16 0h2M5 5l1.5 1.5m11 11L19 19M5 19l1.5-1.5m11-11L19 5" /></Icon>
      : <Icon><path d="M20.5 14A8.5 8.5 0 0 1 10 3.5 8.5 8.5 0 1 0 20.5 14Z" /></Icon>}
  </button>;
}

function HeaderTools() {
  const auth = useAuth();
  const [open, setOpen] = useState(false);
  const [pending, setPending] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const container = useRef<HTMLDivElement>(null);
  const trigger = useRef<HTMLButtonElement>(null);
  const id = useId();
  useEffect(() => {
    if (!open) return;
    function outside(event: PointerEvent) { if (!container.current?.contains(event.target as Node)) setOpen(false); }
    function escape(event: KeyboardEvent) { if (event.key === "Escape") { setOpen(false); trigger.current?.focus(); } }
    document.addEventListener("pointerdown", outside);
    document.addEventListener("keydown", escape);
    return () => { document.removeEventListener("pointerdown", outside); document.removeEventListener("keydown", escape); };
  }, [open]);
  return <div className="header-tools">
    <nav aria-label="Tools" className="header-tool-links">
      <NavLink className="header-control header-nav-link" to="/inventory" aria-label="Search inventory" title="Search inventory">
        <Icon><circle cx="10.5" cy="10.5" r="6.5" /><path d="m16 16 4.5 4.5" /></Icon><span className="header-link-label">Search inventory</span>
      </NavLink>
      <NavLink className="header-control header-nav-link" to="/history" aria-label="Activity" title="Activity">
        <Icon><path d="M3 12h4l3-8 4 16 3-8h4" /></Icon><span className="header-link-label">Activity</span>
      </NavLink>
    </nav>
    <span className="header-tools-divider" aria-hidden="true" />
    <ThemeToggle />
    <div ref={container} className="header-account" onBlur={event => { if (!event.currentTarget.contains(event.relatedTarget as Node)) setOpen(false); }}>
      <button ref={trigger} className="header-control header-account-trigger" aria-expanded={open} aria-controls={id} aria-label={`Account for ${auth.user?.username}`} onClick={() => setOpen(value => !value)}>
        <span className="header-avatar" aria-hidden="true">{auth.user?.username.slice(0, 1).toUpperCase()}</span>
        <span className="header-username">{auth.user?.username}</span>
        <Icon><path d={open ? "m8 14 4-4 4 4" : "m8 10 4 4 4-4"} /></Icon>
      </button>
      {open && <div id={id} className="header-account-dropdown">
        <div className="header-account-info"><strong>{auth.user?.username}</strong><span>{auth.user?.role}</span></div>
        <Link to="/account" className="header-dropdown-item" onClick={() => setOpen(false)}><Icon><circle cx="12" cy="8" r="3" /><path d="M5 21v-2a7 7 0 0 1 14 0v2" /></Icon>Account settings</Link>
        <button className="header-dropdown-item" disabled={pending} onClick={async () => { setPending(true); setError(null); try { await auth.logout(); } catch (reason) { setError(reason instanceof Error ? reason.message : "Sign-out failed"); } finally { setPending(false); } }}>
          <Icon><path d="M9 4H4v16h5m7-12 4 4-4 4m-7-4h11" /></Icon>{pending ? "Signing out…" : "Sign out"}
        </button>
        {error && <p role="alert" className="header-account-error">{error}</p>}
      </div>}
    </div>
  </div>;
}

export default function PageShell({ crumbs, title, actions, children }: { crumbs: Crumb[]; title: string; actions?: ReactNode; children: ReactNode }) {
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
        <HeaderTools />
      </header>
      <main style={{ padding: space.xl }}>
        <div style={{ display: "flex", flexWrap: "wrap", alignItems: "center", justifyContent: "space-between", gap: space.md, marginBottom: space.lg }}>
          <h1 style={{ margin: 0, fontSize: fontSize.xl, fontWeight: 600, letterSpacing: "-0.025em", color: colors.textPrimary }}>{title}</h1>
          {actions && <div style={{ display: "flex", flexWrap: "wrap", alignItems: "center", gap: space.sm }}>{actions}</div>}
        </div>
        {children}
      </main>
    </div>
  );
}
