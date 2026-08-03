import { PowerState } from "../api/types";
import { isTransient } from "./powerColors";

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
    <div style={{ display: "flex", gap: 8 }}>
      <button disabled={disabled || powerState === "on"} onClick={() => onAction("on")}>
        Power On
      </button>
      <button disabled={disabled || powerState === "off"} onClick={() => onAction("off")}>
        Power Off
      </button>
      <button disabled={disabled} onClick={() => onAction("cycle")}>
        Power Cycle
      </button>
    </div>
  );
}
