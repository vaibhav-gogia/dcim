import { useState } from "react";
import DeleteSystem from "./DeleteSystem";
import { InventoryButton } from "./InventoryEditor";
import { usePermissions } from "../AuthContext";
import ActionHistory from "./ActionHistory";
import { usePowerAction, useSystemDetail, useSystemHealth } from "../api/hooks";
import { colors, fontSize, radius, space } from "../theme";
import PowerActionButtons from "./PowerActionButtons";
import { FanGauge, PsuStatus, TempGauge } from "./SensorGauge";
import StatusBadge from "./StatusBadge";
import PowerWiring from "./PowerWiring";

function SectionLabel({ children }: { children: string }) {
  return (
    <div style={{ fontSize: fontSize.xs, fontWeight: 600, letterSpacing: 0.4, textTransform: "uppercase", color: colors.textMuted, margin: `${space.lg}px 0 ${space.sm}px` }}>
      {children}
    </div>
  );
}

export default function SystemDetailPanel({
  systemId,
  rackId,
  onClose,
}: {
  systemId: string;
  rackId: string;
  onClose: () => void;
}) {
  const [deletingId, setDeletingId] = useState<string | null>(null);
  const { canOperate, canManage } = usePermissions();
  const { data: system } = useSystemDetail(systemId);
  const { data: health } = useSystemHealth(systemId);
  const powerAction = usePowerAction(systemId, rackId);

  if (!system) return null;
  const powerState = health?.power_state ?? system.power_state;

  return (
    <div
      style={{
        width: 380,
        padding: space.lg,
        background: colors.surface1,
        border: `1px solid ${colors.border}`,
        borderRadius: radius.md,
      }}
    >
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "start" }}>
        <h3 style={{ margin: 0, fontSize: fontSize.xl, color: colors.textPrimary }}>{system.name}</h3>
        <button
          onClick={onClose}
          style={{ background: "none", border: "none", color: colors.textMuted, fontSize: fontSize.xl, cursor: "pointer", lineHeight: 1 }}
        >
          ×
        </button>
      </div>
      <div style={{ fontSize: fontSize.sm, color: colors.textMuted, marginBottom: space.md }}>
        {system.system_type} · U{system.u_position}-{system.u_position + system.u_height - 1}
      </div>

      <StatusBadge state={powerState} />

      <div style={{ marginTop: space.md }}>
        {canOperate ? <PowerActionButtons powerState={powerState} onAction={(action) => {
          if (action !== "on" && !window.confirm(`${action === "off" ? "Power off" : "Power cycle"} ${system.name}? This interrupts its workloads.`)) return;
          powerAction.mutate(action);
        }} pending={powerAction.isPending} /> : <p>Viewer access · power controls are read-only.</p>}
      </div>

      {powerAction.error && <p role="alert" style={{ color: colors.statusCritical }}>{powerAction.error.message}</p>}
      {canManage && <div style={{ marginTop: space.md }}>
        <InventoryButton type="button" disabled={powerAction.isPending} style={{ color: colors.statusCritical }} onClick={() => setDeletingId(systemId)}>Delete system</InventoryButton>
        {deletingId === systemId && <DeleteSystem key={systemId} systemId={systemId} name={system.name} onDeleted={onClose} onCancel={() => setDeletingId(null)} />}
      </div>}
      <PowerWiring key={systemId} systemId={systemId} rackId={rackId} />

      <ActionHistory key={systemId} systemId={systemId} />
      {health && (
        <div>
          <SectionLabel>Temperatures</SectionLabel>
          {Object.entries(health.temps_c).map(([label, value]) => (
            <TempGauge key={label} label={label} value={value} />
          ))}

          <SectionLabel>Fans</SectionLabel>
          {Object.entries(health.fans_rpm).map(([label, rpm]) => (
            <FanGauge key={label} label={label} rpm={rpm} />
          ))}

          <SectionLabel>PSUs</SectionLabel>
          {Object.entries(health.psus).map(([label, status]) => (
            <PsuStatus key={label} label={label} status={status} />
          ))}
        </div>
      )}
    </div>
  );
}
