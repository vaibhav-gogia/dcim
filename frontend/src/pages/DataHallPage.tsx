import HallLayoutEditor from "../components/HallLayoutEditor";
import { useState } from "react";
import { useParams } from "react-router-dom";
import { useDataHallFloor } from "../api/hooks";
import InventoryEditor, { dataHallFields, rackFields, InventoryButton } from "../components/InventoryEditor";
import DataCenterFloorView from "../components/DataCenterFloorView";
import PageShell from "../components/PageShell";

export default function DataHallPage() {
  const { dataHallId } = useParams<{ dataHallId: string }>();
  const { data: hall, error } = useDataHallFloor(dataHallId!);
  const [layoutEditing, setLayoutEditing] = useState(false);
  const [editor, setEditor] = useState<"hall" | "rack" | null>(null);
  if (error) return <PageShell crumbs={[{ label: "Data Centers", to: "/" }]} title="Unable to load data hall"><p role="alert">{error.message}</p></PageShell>;
  if (!hall) return <PageShell crumbs={[{ label: "Data Centers", to: "/" }]} title="Loading…"><p role="status">Loading floor plan…</p></PageShell>;
  return <PageShell crumbs={[{ label: "Data Centers", to: "/" }, { label: hall.datacenter_name, to: `/dc/${hall.datacenter_id}` }, { label: hall.name }]} title={hall.name}
    actions={<><InventoryButton disabled={layoutEditing} onClick={() => setEditor("hall")}>Edit data hall</InventoryButton><InventoryButton disabled={layoutEditing} onClick={() => setEditor("rack")}>Add rack</InventoryButton><InventoryButton disabled={layoutEditing || !hall.racks.length} onClick={() => { setEditor(null); setLayoutEditing(true); }}>Edit layout</InventoryButton></>}>
    {editor && <InventoryEditor key={editor} title={editor === "hall" ? "Edit data hall" : "Add rack"}
      path={editor === "hall" ? `/data-halls/${hall.id}` : `/data-halls/${hall.id}/racks`}
      editing={editor === "hall"} fields={editor === "hall" ? dataHallFields : rackFields} onClose={() => setEditor(null)} />}
    {!layoutEditing && <p>{hall.racks.length ? "Click a rack to view it." : "No racks yet. Add a rack to start building this hall’s floor plan."}</p>}
    {layoutEditing ? <HallLayoutEditor key={hall.id} hallId={hall.id} racks={hall.racks} onClose={() => setLayoutEditing(false)} /> : <DataCenterFloorView racks={hall.racks} />}
  </PageShell>;
}
