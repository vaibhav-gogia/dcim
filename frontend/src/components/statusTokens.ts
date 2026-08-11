import { colors } from "../theme";
import { PowerState } from "../api/types";

export interface StatusToken {
  color: string;
  glyph: string;
  label: string;
}

export const POWER_STATUS: Record<PowerState, StatusToken> = {
  on: { color: colors.statusGood, glyph: "●", label: "on" },
  off: { color: colors.off, glyph: "○", label: "off" },
  booting: { color: colors.statusWarning, glyph: "◐", label: "booting" },
  shutting_down: { color: colors.statusWarning, glyph: "◐", label: "shutting down" },
  cycling: { color: colors.statusWarning, glyph: "◐", label: "cycling" },
  unknown: { color: colors.statusCritical, glyph: "!", label: "unknown" },
};

export const TRANSIENT_STATES: PowerState[] = ["booting", "shutting_down", "cycling"];

export function isTransient(state: PowerState): boolean {
  return TRANSIENT_STATES.includes(state);
}
