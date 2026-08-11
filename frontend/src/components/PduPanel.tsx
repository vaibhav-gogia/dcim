import { useOutletAction, useRackPdus } from "../api/hooks";
import { PDUWithOutlets } from "../api/types";
import { colors, fontSize, radius, space } from "../theme";

export default function PduPanel({ rackId }: { rackId: string }) {
  const { data: pdus } = useRackPdus(rackId);

  if (!pdus) return null;

  return (
    <div style={{ width: 340 }}>
      {pdus.map((pdu) => (
        <PduCard key={pdu.id} pdu={pdu} rackId={rackId} />
      ))}
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

  return (
    <div
      style={{
        marginBottom: space.lg,
        padding: space.md,
        background: colors.surface1,
        border: `1px solid ${colors.border}`,
        borderRadius: radius.md,
      }}
    >
      <div style={{ fontWeight: 600, fontSize: fontSize.md, marginBottom: space.sm, color: colors.textPrimary }}>{pdu.name}</div>
      <div style={{ display: "grid", gridTemplateColumns: "repeat(4, 1fr)", gap: 8 }}>
        {pdu.outlets.map((outlet) => (
          <div
            key={outlet.id}
            title={outlet.connected_system_name ?? "unconnected"}
            style={{
              padding: "6px 2px",
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
          </div>
        ))}
      </div>
      <Legend />
    </div>
  );
}
