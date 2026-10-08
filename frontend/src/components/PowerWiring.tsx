import { useState } from "react";
import { usePowerConnections, useRackPdus, useUnwirePower, useWirePower } from "../api/hooks";
import { colors, fontSize, radius, space } from "../theme";
import { InventoryButton } from "./InventoryEditor";

export default function PowerWiring({ systemId, rackId }: { systemId: string; rackId: string }) {
  const connections = usePowerConnections(systemId);
  const pdus = useRackPdus(rackId);
  const wire = useWirePower(systemId);
  const unwire = useUnwirePower();
  const [label, setLabel] = useState("PSU1");
  const [outletId, setOutletId] = useState("");
  const pending = wire.isPending || unwire.isPending;
  const available = (pdus.data ?? []).flatMap(pdu => pdu.outlets.filter(o => !o.connected_system_id).map(outlet => ({ ...outlet, pduName: pdu.name })));
  const outletNames = new Map((pdus.data ?? []).flatMap(pdu => pdu.outlets.map(o => [o.id, `${pdu.name} · outlet ${o.outlet_number}`] as const)));
  const error = connections.error ?? pdus.error;
  const inputStyle = { width: "100%", padding: space.sm, border: `1px solid ${colors.border}`, borderRadius: radius.sm, background: colors.surface0, color: colors.textPrimary, fontSize: fontSize.sm };

  return <section aria-label="Power connections" style={{ borderTop: `1px solid ${colors.border}`, marginTop: space.lg, paddingTop: space.md }}>
    <h4 style={{ margin: `0 0 ${space.sm}px` }}>Power connections</h4>
    <p style={{ color: colors.textMuted, fontSize: fontSize.xs }}>Label each PSU and assign an outlet. For A/B wiring, choose outlets on separate PDUs. Hardware is simulated.</p>
    {error ? <p role="alert">{error.message}</p> : !connections.data || !pdus.data ? <p role="status">Loading wiring…</p> : <>
      {!connections.data.length && <p>No power connections yet.</p>}
      {connections.data.map(connection => <div key={connection.id} style={{ marginBottom: space.md }}>
        <strong>{connection.psu_label ?? "Unlabeled PSU"}</strong>
        <div style={{ fontSize: fontSize.sm, marginBottom: space.xs }}>{outletNames.get(connection.pdu_outlet_id) ?? "Loading outlet…"}</div>
        <InventoryButton disabled={pending} onClick={() => { wire.reset(); unwire.mutate(connection.id); }}>Disconnect</InventoryButton>
      </div>)}
      {!pdus.data.length ? <p>Add a PDU to this rack to connect its systems.</p> : !available.length ? <p>All outlets are assigned. Add another PDU or disconnect an outlet.</p> :
        <form onSubmit={event => { event.preventDefault(); unwire.reset(); wire.mutate({ pdu_outlet_id: outletId, psu_label: label.trim() }, { onSuccess: () => { setOutletId(""); setLabel(""); } }); }}>
          <fieldset disabled={pending} style={{ border: 0, padding: 0, margin: 0, display: "grid", gap: space.sm }}>
            <label>PSU label<input style={inputStyle} required maxLength={32} pattern=".*\S.*" value={label} placeholder="PSU1 or PSU2" onChange={e => setLabel(e.target.value)} /></label>
            <label>Available outlet<select style={inputStyle} required value={outletId} onChange={e => setOutletId(e.target.value)}>
              <option value="">Choose an outlet</option>
              {available.map(o => <option key={o.id} value={o.id}>{o.pduName} · outlet {o.outlet_number} ({o.state})</option>)}
            </select></label>
            <InventoryButton type="submit">{wire.isPending ? "Connecting…" : "Connect PSU"}</InventoryButton>
          </fieldset>
        </form>}
    </>}
    {(wire.error || unwire.error) && <p role="alert" style={{ color: colors.statusCritical }}>{(wire.error ?? unwire.error)?.message}</p>}
    {wire.isSuccess && <p role="status">PSU connected.</p>}
    {unwire.isSuccess && <p role="status">PSU disconnected. Outlet power was not changed.</p>}
  </section>;
}
