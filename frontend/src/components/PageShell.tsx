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
  return (
    <div style={{ minHeight: "100vh" }}>
      <header
        style={{
          padding: `${space.md}px ${space.xl}px`,
          borderBottom: `1px solid ${colors.border}`,
          display: "flex",
          alignItems: "center",
          justifyContent: "space-between",
        }}
      >
        <div>
          <div style={{ fontSize: fontSize.sm, color: colors.textMuted, marginBottom: 2 }}>
            {crumbs.map((crumb, i) => (
              <span key={i}>
                {i > 0 && " / "}
                {crumb.to ? (
                  <Link to={crumb.to} style={{ color: colors.textMuted, textDecoration: "none" }}>
                    {crumb.label}
                  </Link>
                ) : (
                  <span style={{ color: colors.textSecondary }}>{crumb.label}</span>
                )}
              </span>
            ))}
          </div>
          <h1 style={{ margin: 0, fontSize: fontSize.xxl, color: colors.textPrimary }}>{title}</h1>
        </div>
        <div style={{ display: "flex", alignItems: "center", gap: space.sm }}>
          {actions}
          <ThemeToggle />
        </div>
      </header>
      <main style={{ padding: space.xl }}>{children}</main>
    </div>
  );
}
