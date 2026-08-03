import { useOutletAction, useRackPdus } from "../api/hooks";
import { PDUWithOutlets } from "../api/types";

export default function PduPanel({ rackId }: { rackId: string }) {
  const { data: pdus } = useRackPdus(rackId);

  if (!pdus) return null;

  return (
    <div style={{ width: 260 }}>
      {pdus.map((pdu) => (
        <PduCard key={pdu.id} pdu={pdu} rackId={rackId} />
      ))}
    </div>
  );
}

function PduCard({ pdu, rackId }: { pdu: PDUWithOutlets; rackId: string }) {
  const outletAction = useOutletAction(pdu.id, rackId);

  return (
    <div
      style={{
        marginBottom: 16,
        padding: 12,
        background: "#1a2029",
        border: "1px solid #4a5568",
        borderRadius: 8,
      }}
    >
      <div style={{ fontWeight: 600, marginBottom: 8 }}>{pdu.name}</div>
      <div style={{ display: "grid", gridTemplateColumns: "repeat(4, 1fr)", gap: 6 }}>
        {pdu.outlets.map((outlet) => (
          <div
            key={outlet.id}
            title={outlet.connected_system_name ?? "unconnected"}
            style={{
              padding: "4px 2px",
              textAlign: "center",
              fontSize: 10,
              borderRadius: 4,
              background: outlet.state === "on" ? "#2e8b57" : "#3a4350",
              color: outlet.state === "on" ? "#0f1319" : "#9aa5b1",
              cursor: "pointer",
            }}
            onClick={() =>
              outletAction.mutate({ outletId: outlet.id, action: outlet.state === "on" ? "off" : "on" })
            }
          >
            {outlet.outlet_number}
          </div>
        ))}
      </div>
    </div>
  );
}
