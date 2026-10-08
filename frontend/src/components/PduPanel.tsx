import { useState } from "react";
import InventoryEditor, { pduFields, pduEditFields, InventoryButton } from "./InventoryEditor";
import { useOutletAction, useRackPdus } from "../api/hooks";
import { PDUWithOutlets } from "../api/types";
import { colors, fontSize, radius, space } from "../theme";

export default function PduPanel({ rackId }: { rackId: string }) {
  const { data: pdus, error, isPending } = useRackPdus(rackId);
  const [adding, setAdding] = useState(false);

  return (
    <div style={{ flex: "1 1 340px", minWidth: "min(340px, 100%)", maxWidth: 700 }}>
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: space.md }}>
        <h3 style={{ margin: 0, fontSize: fontSize.lg }}>PDUs</h3>
        <InventoryButton onClick={() => setAdding(true)}>Add PDU</InventoryButton>
      </div>
      {adding && <InventoryEditor title="Add PDU" path={`/racks/${rackId}/pdus`} fields={pduFields} onClose={() => setAdding(false)} />}
      {isPending && <p role="status">Loading PDUs…</p>}
      {error && <p role="alert">{error.message}</p>}
      {pdus?.length === 0 && <p>No PDUs yet. Add PDU A and PDU B to wire redundant PSUs.</p>}
      <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(min(100%, 340px), 1fr))", gap: space.lg, alignItems: "start" }}>
        {pdus?.map((pdu) => (
          <PduCard key={pdu.id} pdu={pdu} rackId={rackId} />
        ))}
      </div>
    </div>
  );
}

function Legend() {
  return (
    <div style={{ display: "flex", gap: space.md, fontSize: fontSize.xs, color: colors.textMuted, marginTop: space.sm }}>
      <span>
        <span style={{ color: colors.statusGood }}>●</span> on
      </span>
      <span>
        <span style={{ color: colors.textMuted }}>○</span> off
      </span>
    </div>
  );
}

function PduCard({ pdu, rackId }: { pdu: PDUWithOutlets; rackId: string }) {
  const outletAction = useOutletAction(pdu.id, rackId);
  const [editing, setEditing] = useState(false);

  return (
    <div
      style={{
        padding: space.md,
        background: colors.surface1,
        border: `1px solid ${colors.border}`,
        borderRadius: radius.md,
      }}
    >
      <div style={{ fontWeight: 600, fontSize: fontSize.md, marginBottom: space.sm, color: colors.textPrimary }}>{pdu.name}</div>
      <div style={{ marginBottom: space.sm, fontSize: fontSize.xs, color: colors.textMuted }}>{pdu.outlet_count} outlets · simulated</div>
      <InventoryButton style={{ marginBottom: space.md }} onClick={() => setEditing(true)}>Edit PDU</InventoryButton>
      {editing && <InventoryEditor title="Edit PDU" path={`/pdus/${pdu.id}`} editing fields={pduEditFields} onClose={() => setEditing(false)} />}
      {outletAction.error && <p role="alert" style={{ color: colors.statusCritical }}>{outletAction.error.message}</p>}
      <div style={{ display: "grid", gridTemplateColumns: "repeat(4, 1fr)", gap: 8 }}>
        {pdu.outlets.map((outlet) => (
          <button
            type="button"
            disabled={outletAction.isPending}
            aria-label={`Outlet ${outlet.outlet_number}, ${outlet.state}, ${outlet.connected_system_name ?? "unassigned"}. Turn ${outlet.state === "on" ? "off" : "on"}`}
            key={outlet.id}
            title={outlet.connected_system_name ?? "unconnected"}
            style={{
              padding: "6px 2px",
              border: `1px solid ${colors.border}`,
              textAlign: "center",
              fontSize: fontSize.xs,
              borderRadius: radius.sm,
              background: outlet.state === "on" ? colors.statusGood : colors.surface2,
              color: outlet.state === "on" ? "#06280a" : colors.textMuted,
              cursor: "pointer",
              userSelect: "none",
            }}
            onClick={() => outletAction.mutate({ outletId: outlet.id, action: outlet.state === "on" ? "off" : "on" })}
          >
            {outlet.outlet_number}
          </button>
        ))}
      </div>
      <Legend />
      <div style={{ fontSize: fontSize.xs, color: colors.textSecondary, marginTop: space.md }}>
        {pdu.outlets.filter(o => o.connected_system_id).map(o => <div key={o.id}>Outlet {o.outlet_number} → {o.connected_system_name}</div>)}
      </div>
    </div>
  );
}
