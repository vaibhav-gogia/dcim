import { usePowerAction, useSystemDetail, useSystemHealth } from "../api/hooks";
import { POWER_STATE_COLOR } from "./powerColors";
import PowerActionButtons from "./PowerActionButtons";
import { FanGauge, PsuStatus, TempGauge } from "./SensorGauge";

export default function SystemDetailPanel({
  systemId,
  rackId,
  onClose,
}: {
  systemId: string;
  rackId: string;
  onClose: () => void;
}) {
  const { data: system } = useSystemDetail(systemId);
  const { data: health } = useSystemHealth(systemId);
  const powerAction = usePowerAction(systemId, rackId);

  if (!system) return null;

  return (
    <div
      style={{
        width: 300,
        padding: 16,
        background: "#1a2029",
        border: "1px solid #4a5568",
        borderRadius: 8,
      }}
    >
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "start" }}>
        <h3 style={{ margin: 0 }}>{system.name}</h3>
        <button onClick={onClose}>×</button>
      </div>
      <div style={{ fontSize: 12, color: "#9aa5b1", marginBottom: 8 }}>
        {system.system_type} · U{system.u_position}-{system.u_position + system.u_height - 1}
      </div>

      <div
        style={{
          display: "inline-block",
          padding: "2px 8px",
          borderRadius: 4,
          background: POWER_STATE_COLOR[(health?.power_state ?? system.power_state)],
          color: "#0f1319",
          fontSize: 12,
          marginBottom: 12,
        }}
      >
        {health?.power_state ?? system.power_state}
      </div>

      <PowerActionButtons
        powerState={health?.power_state ?? system.power_state}
        onAction={(action) => powerAction.mutate(action)}
        pending={powerAction.isPending}
      />

      {health && (
        <div style={{ marginTop: 16 }}>
          <div style={{ fontSize: 12, fontWeight: 600, marginBottom: 4 }}>Temperatures</div>
          {Object.entries(health.temps_c).map(([label, value]) => (
            <TempGauge key={label} label={label} value={value} />
          ))}

          <div style={{ fontSize: 12, fontWeight: 600, margin: "12px 0 4px" }}>Fans</div>
          {Object.entries(health.fans_rpm).map(([label, rpm]) => (
            <FanGauge key={label} label={label} rpm={rpm} />
          ))}

          <div style={{ fontSize: 12, fontWeight: 600, margin: "12px 0 4px" }}>PSUs</div>
          {Object.entries(health.psus).map(([label, status]) => (
            <PsuStatus key={label} label={label} status={status} />
          ))}
        </div>
      )}
    </div>
  );
}
