// Colors reference CSS custom properties (defined in index.css for both
// light and dark) so every component that imports `colors` stays theme-aware
// without needing to know which mode is active. Status colors are fixed —
// per the palette spec they're mode-invariant (paired with icon + label).
export const colors = {
  surface0: "var(--surface-0)", // page plane
  surface1: "var(--surface-1)", // card / chart surface
  surface2: "var(--surface-2)", // hover / elevated
  textPrimary: "var(--text-primary)",
  textSecondary: "var(--text-secondary)",
  textMuted: "var(--text-muted)",
  border: "var(--border)",
  gridline: "var(--gridline)",
  accent: "var(--accent)", // categorical slot-1 / sequential blue anchor
  accentTrack: "var(--accent-track)",
  off: "var(--off)", // neutral "off" tone — not a status color, off isn't an alarm
  successText: "var(--success-text)", // higher-contrast green for "ok" text specifically
  statusGood: "#0ca30c",
  statusWarning: "#fab219",
  statusSerious: "#ec835a",
  statusCritical: "#d03b3b",
} as const;

// Bumped ~1.25x across the board (space, radius, fontSize) to read like the
// app at 125% browser zoom by default — applies everywhere EXCEPT RackElevation.tsx,
// which intentionally uses its own literal sizes so its rack proportions stay locked.
export const space = { xs: 5, sm: 10, md: 15, lg: 20, xl: 30 } as const;

export const radius = { sm: 5, md: 10 } as const;

export const font = {
  mono: "ui-monospace, SFMono-Regular, Menlo, monospace",
} as const;

// Shared type scale — use these everywhere instead of ad-hoc fontSize numbers,
// so a readability pass is a one-file change, not a hunt across components.
export const fontSize = {
  micro: 11, // dense inline SVG annotations
  xs: 13, // compact labels: legends, outlet tile numbers, floor rack subtitle
  sm: 14, // default UI text: buttons, table cells, meta rows, breadcrumbs
  md: 16, // meter/section labels, card subtitles, PDU name
  lg: 19, // card + rack system names
  xl: 21, // panel header (system detail name)
  xxl: 26, // page title
} as const;
