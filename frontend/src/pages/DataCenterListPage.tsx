import { useState } from "react";
import InventoryEditor, { dataCenterFields, InventoryButton } from "../components/InventoryEditor";
import { useNavigate } from "react-router-dom";

import { useDataCenters } from "../api/hooks";
import PageShell from "../components/PageShell";
import { colors, fontSize, radius, space } from "../theme";

export default function DataCenterListPage() {
  const navigate = useNavigate();
  const [adding, setAdding] = useState(false);
  const [editing, setEditing] = useState<string | null>(null);
  const { data: datacenters, isLoading, error } = useDataCenters();

  return (
    <PageShell crumbs={[{ label: "DCIM" }]} title="Data Centers" actions={<InventoryButton onClick={() => { setEditing(null); setAdding(true); }}>Add data center</InventoryButton>}>
      {(adding || editing) && <InventoryEditor key={editing ?? "new"} title={editing ? "Edit data center" : "Add data center"} path={editing ? `/datacenters/${editing}` : "/datacenters"} editing={!!editing} fields={dataCenterFields} onClose={() => { setAdding(false); setEditing(null); }} />}
      {error ? <p role="alert">{error.message}</p> : isLoading ? (
        <div style={{ color: colors.textMuted }}>Loading...</div>
      ) : !datacenters?.length ? (
        <div style={{ color: colors.textMuted }}>No data centers yet.</div>
      ) : (
        <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fill, minmax(275px, 1fr))", gap: space.lg, maxWidth: 1100 }}>
          {datacenters.map((dc) => (
            <div
              key={dc.id}
              style={{
                padding: space.lg,
                background: colors.surface1,
                border: `1px solid ${colors.border}`,
                borderRadius: radius.md,
              }}
            >
              <InventoryButton onClick={() => navigate(`/dc/${dc.id}`)} style={{ width: "100%", textAlign: "left", marginBottom: space.sm }}>Open data center</InventoryButton>
              <div style={{ fontSize: fontSize.lg, fontWeight: 600, color: colors.textPrimary, marginBottom: space.xs }}>{dc.name}</div>
              {dc.location && <div style={{ fontSize: fontSize.sm, color: colors.textMuted }}>{dc.location}</div>}
              <InventoryButton style={{ marginTop: space.md }} onClick={() => { setAdding(false); setEditing(dc.id); }}>Edit</InventoryButton>
            </div>
          ))}
        </div>
      )}
    </PageShell>
  );
}
