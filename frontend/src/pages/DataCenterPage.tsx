import { useState } from "react";
import { Link, useParams } from "react-router-dom";
import { useDataCenter, useDataHalls } from "../api/hooks";
import InventoryEditor, { dataCenterFields, dataHallFields, InventoryButton } from "../components/InventoryEditor";
import PageShell from "../components/PageShell";
import { colors, fontSize, radius, space } from "../theme";

export default function DataCenterPage() {
  const { datacenterId } = useParams<{ datacenterId: string }>();
  const center = useDataCenter(datacenterId!);
  const halls = useDataHalls(datacenterId!);
  const [editor, setEditor] = useState<"dc" | "hall" | null>(null);
  const error = center.error ?? halls.error;
  if (error) return <PageShell crumbs={[{ label: "Data Centers", to: "/" }]} title="Unable to load data center"><p role="alert">{error.message}</p></PageShell>;
  if (!center.data || !halls.data) return <PageShell crumbs={[{ label: "Data Centers", to: "/" }]} title="Loading…"><p role="status">Loading data halls…</p></PageShell>;
  const dc = center.data;
  return (
    <PageShell crumbs={[{ label: "Data Centers", to: "/" }, { label: dc.name }]} title={dc.name}
      actions={<><InventoryButton onClick={() => setEditor("dc")}>Edit data center</InventoryButton><InventoryButton onClick={() => setEditor("hall")}>Add data hall</InventoryButton></>}>
      {editor && <InventoryEditor key={editor} title={editor === "dc" ? "Edit data center" : "Add data hall"}
        path={editor === "dc" ? `/datacenters/${dc.id}` : `/datacenters/${dc.id}/data-halls`}
        editing={editor === "dc"} fields={editor === "dc" ? dataCenterFields : dataHallFields} onClose={() => setEditor(null)} />}
      {dc.location && <p style={{ color: colors.textMuted }}>{dc.location}</p>}
      <h2 style={{ fontSize: fontSize.xl }}>Data halls</h2>
      {!halls.data.length ? <p>No data halls yet. Add a data hall, then add its racks.</p> :
        <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fill, minmax(275px, 1fr))", gap: space.lg, maxWidth: 1100 }}>
          {halls.data.map(hall => <Link key={hall.id} to={`/hall/${hall.id}`} style={{ display: "block", padding: space.lg, border: `1px solid ${colors.border}`, borderRadius: radius.md, background: colors.surface1, color: colors.textPrimary, textDecoration: "none" }}>
            <strong style={{ fontSize: fontSize.lg }}>{hall.name}</strong>
            <div style={{ marginTop: space.sm, color: colors.textMuted }}>View rack floor plan →</div>
          </Link>)}
        </div>}
    </PageShell>
  );
}
