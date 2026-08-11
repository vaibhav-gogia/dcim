import { ReactNode } from "react";

import { PowerState } from "../api/types";
import { isTransient } from "./statusTokens";
import { colors, fontSize, radius } from "../theme";

function ActionButton({ children, disabled, onClick }: { children: ReactNode; disabled: boolean; onClick: () => void }) {
  return (
    <button
      disabled={disabled}
      onClick={onClick}
      style={{
        flex: 1,
        padding: "7px 10px",
        fontSize: fontSize.sm,
        borderRadius: radius.sm,
        border: `1px solid ${colors.border}`,
        background: colors.surface2,
        color: disabled ? colors.textMuted : colors.textPrimary,
        cursor: disabled ? "not-allowed" : "pointer",
        opacity: disabled ? 0.5 : 1,
      }}
    >
      {children}
    </button>
  );
}

export default function PowerActionButtons({
  powerState,
  onAction,
  pending,
}: {
  powerState: PowerState;
  onAction: (action: "on" | "off" | "cycle") => void;
  pending: boolean;
}) {
  const disabled = pending || isTransient(powerState);

  return (
    <div style={{ display: "flex", gap: 6 }}>
      <ActionButton disabled={disabled || powerState === "on"} onClick={() => onAction("on")}>
        Power On
      </ActionButton>
      <ActionButton disabled={disabled || powerState === "off"} onClick={() => onAction("off")}>
        Power Off
      </ActionButton>
      <ActionButton disabled={disabled} onClick={() => onAction("cycle")}>
        Power Cycle
      </ActionButton>
    </div>
  );
}
