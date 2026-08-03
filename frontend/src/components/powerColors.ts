import { PowerState } from "../api/types";

export const POWER_STATE_COLOR: Record<PowerState, string> = {
  on: "#2e8b57",
  off: "#8a8a8a",
  booting: "#d4a017",
  shutting_down: "#d4a017",
  cycling: "#d4a017",
  unknown: "#b04040",
};

export const TRANSIENT_STATES: PowerState[] = ["booting", "shutting_down", "cycling"];

export function isTransient(state: PowerState): boolean {
  return TRANSIENT_STATES.includes(state);
}
