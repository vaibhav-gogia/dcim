import { PowerState } from "../api/types";
import { POWER_STATUS } from "./statusTokens";
import { colors, fontSize as fontScale, radius, space } from "../theme";

export default function StatusBadge({
  state,
  size = "md",
}: {
  state: PowerState;
  size?: "sm" | "md";
}) {
  const token = POWER_STATUS[state];
  const textSize = size === "sm" ? fontScale.xs : fontScale.sm;

  return (
    <span
      style={{
        display: "inline-flex",
        alignItems: "center",
        gap: space.xs,
        padding: `2px ${space.sm}px`,
        borderRadius: radius.sm,
        background: colors.surface2,
        border: `1px solid ${colors.border}`,
        fontSize: textSize,
        color: colors.textPrimary,
        lineHeight: 1.6,
      }}
    >
      <span style={{ color: token.color }}>{token.glyph}</span>
      {token.label}
    </span>
  );
}
