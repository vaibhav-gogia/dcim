import { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { Link } from "react-router-dom";
import { api } from "../api/client";
import { colors, fontSize, radius, space } from "../theme";
import { InventoryButton } from "./InventoryEditor";

interface Event { id: string; actor: string; action: string; target: string; created_at: string; outcome: string; message: string; changed_fields: string[] }
export default function ActionHistory({ rackId, systemId }: { rackId?: string; systemId?: string }) {
  const [offset, setOffset] = useState(0);
  const params = new URLSearchParams({ offset: String(offset), limit: "15" });
  if (rackId) params.set("rack_id", rackId);
  if (systemId) params.set("system_id", systemId);
  const query = useQuery({ queryKey: ["history", params.toString()], queryFn: () => api.get<{ total: number; items: Event[] }>(`/history?${params}`), refetchInterval: 5000 });
  return <section aria-label="Action history" style={{ marginTop: space.xl }}>
    <h3 style={{ marginTop: 0 }}>Action history</h3>
    {query.isPending ? <p role="status">Loading history…</p> : query.error ? <p role="alert">{query.error.message}</p> : query.data && <>
      {!query.data.items.length ? <p>No recorded actions yet.</p> : <div style={{ overflowX: "auto", background: colors.surface1, border: `1px solid ${colors.border}`, borderRadius: radius.sm }}>
        <table style={{ width: "100%", textAlign: "left", fontSize: fontSize.sm }}>
          <thead><tr>{["When", "Who", "Action / target", "Outcome"].map(h => <th key={h} scope="col" style={{ padding: space.sm }}>{h}</th>)}</tr></thead>
          <tbody>{query.data.items.map(event => <tr key={event.id}>
            <td style={{ padding: space.sm, verticalAlign: "top" }}><time dateTime={event.created_at}>{new Date(event.created_at).toLocaleString()}</time></td>
            <td style={{ padding: space.sm, verticalAlign: "top" }}>{event.actor}</td>
            <td style={{ padding: space.sm }}><strong>{event.target}</strong><div style={{ overflowWrap: "anywhere" }}>{event.action}</div>{!!event.changed_fields.length && <small>Fields: {event.changed_fields.join(", ")}</small>}</td>
            <td style={{ padding: space.sm }}><strong style={{ color: ["failed", "unknown"].includes(event.outcome) ? colors.statusCritical : colors.textPrimary }}>{event.outcome}</strong><div>{event.message}</div></td>
          </tr>)}</tbody>
        </table>
      </div>}
      <div style={{ display: "flex", gap: space.sm, marginTop: space.sm }}>
        <InventoryButton disabled={offset === 0} onClick={() => setOffset(Math.max(0, offset - 15))}>Previous</InventoryButton>
        <InventoryButton disabled={offset + 15 >= query.data.total} onClick={() => setOffset(offset + 15)}>Next</InventoryButton>
      </div>
      {(rackId || systemId) && <p><Link to="/history">View all activity</Link></p>}
    </>}
  </section>;
}
