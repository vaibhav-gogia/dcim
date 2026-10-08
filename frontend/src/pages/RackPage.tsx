import InventoryEditor, { rackFields, systemFields, InventoryButton } from "../components/InventoryEditor";
import { useState } from "react";
import { useParams, useSearchParams } from "react-router-dom";

import { useRackElevation } from "../api/hooks";
import { SystemElevation } from "../api/types";
import PageShell from "../components/PageShell";
import PduPanel from "../components/PduPanel";
import RackElevation from "../components/RackElevation";
import SystemDetailPanel from "../components/SystemDetailPanel";
import SystemsTable from "../components/SystemsTable";
import { colors, fontSize, radius, space } from "../theme";

type ViewMode = "visual" | "list";

function ViewToggle({ mode, onChange }: { mode: ViewMode; onChange: (mode: ViewMode) => void }) {
  const options: ViewMode[] = ["visual", "list"];
  return (
    <div style={{ display: "flex", border: `1px solid ${colors.border}`, borderRadius: radius.sm, overflow: "hidden" }}>
      {options.map((opt) => (
        <button
          key={opt}
          onClick={() => onChange(opt)}
          style={{
            padding: "9px 18px",
            fontSize: fontSize.sm,
            border: "none",
            background: mode === opt ? colors.surface2 : "transparent",
            color: mode === opt ? colors.textPrimary : colors.textMuted,
            cursor: "pointer",
            textTransform: "capitalize",
          }}
        >
          {opt}
        </button>
      ))}
    </div>
  );
}

export default function RackPage() {
  const { rackId } = useParams<{ rackId: string }>();
  const [editor, setEditor] = useState<"rack" | "add" | "system" | null>(null);
  const { data: rack, isLoading, error } = useRackElevation(rackId!);
  const [searchParams, setSearchParams] = useSearchParams();
  const selectedSystem = rack?.systems.find(system => system.id === searchParams.get("system")) ?? null;
  function setSelectedSystem(system: SystemElevation | null) {
    setSearchParams(previous => { const next = new URLSearchParams(previous); if (system) next.set("system", system.id); else next.delete("system"); return next; }, { replace: true });
  }
  const [viewMode, setViewMode] = useState<ViewMode>("visual");

  if (error) return <PageShell crumbs={[{ label: "Data Centers", to: "/" }]} title="Unable to load rack"><p role="alert">{error.message}</p></PageShell>;

  if (isLoading || !rack) {
    return (
      <PageShell crumbs={[{ label: "Data Centers", to: "/" }]} title="Loading...">
        <div style={{ color: colors.textMuted }}>Loading...</div>
      </PageShell>
    );
  }

  return (
    <PageShell
      crumbs={[{ label: "Data Centers", to: "/" }, { label: rack.datacenter_name, to: `/dc/${rack.datacenter_id}` }, { label: rack.data_hall_name, to: `/hall/${rack.data_hall_id}` }, { label: rack.name }]}
      title={rack.name}
      actions={<><InventoryButton onClick={() => setEditor("rack")}>Edit rack</InventoryButton><InventoryButton onClick={() => setEditor("add")}>Add system</InventoryButton>{selectedSystem && <InventoryButton onClick={() => setEditor("system")}>Edit selected system</InventoryButton>}<ViewToggle mode={viewMode} onChange={setViewMode} /></>}
    >
      {editor && <InventoryEditor key={`${editor}-${selectedSystem?.id}`} title={editor === "rack" ? "Edit rack" : editor === "add" ? "Add system" : "Edit system"} path={editor === "rack" ? `/racks/${rackId}` : editor === "add" ? `/racks/${rackId}/systems` : `/systems/${selectedSystem!.id}`} editing={editor !== "add"} fields={editor === "rack" ? rackFields : systemFields} onClose={() => setEditor(null)} />}
      {!rack.systems.length && <p>No systems yet. Add a system and set its starting U and height.</p>}
      <div style={{ display: "flex", flexWrap: "wrap", gap: space.xl, alignItems: "flex-start" }}>
        {viewMode === "visual" ? (
          <>
            <RackElevation rack={rack} selectedSystemId={selectedSystem?.id ?? null} onSelectSystem={setSelectedSystem} />
          </>
        ) : (
          <SystemsTable systems={rack.systems} selectedSystemId={selectedSystem?.id ?? null} onSelectSystem={setSelectedSystem} />
        )}
        <PduPanel rackId={rackId!} />
        {selectedSystem && <SystemDetailPanel systemId={selectedSystem.id} rackId={rackId!} onClose={() => setSelectedSystem(null)} />}
      </div>
    </PageShell>
  );
}
