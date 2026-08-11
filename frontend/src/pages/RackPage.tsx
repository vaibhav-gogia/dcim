import { useState } from "react";
import { useParams } from "react-router-dom";

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
  const { data: rack, isLoading } = useRackElevation(rackId!);
  const [selectedSystem, setSelectedSystem] = useState<SystemElevation | null>(null);
  const [viewMode, setViewMode] = useState<ViewMode>("visual");

  if (isLoading || !rack) {
    return (
      <PageShell crumbs={[{ label: "Data Centers", to: "/" }]} title="Loading...">
        <div style={{ color: colors.textMuted }}>Loading...</div>
      </PageShell>
    );
  }

  return (
    <PageShell
      crumbs={[{ label: "Data Centers", to: "/" }, { label: rack.name }]}
      title={rack.name}
      actions={<ViewToggle mode={viewMode} onChange={setViewMode} />}
    >
      <div style={{ display: "flex", gap: space.xl, alignItems: "flex-start" }}>
        {viewMode === "visual" ? (
          <>
            <RackElevation rack={rack} selectedSystemId={selectedSystem?.id ?? null} onSelectSystem={setSelectedSystem} />
            <PduPanel rackId={rackId!} />
          </>
        ) : (
          <SystemsTable systems={rack.systems} selectedSystemId={selectedSystem?.id ?? null} onSelectSystem={setSelectedSystem} />
        )}
        {selectedSystem && <SystemDetailPanel systemId={selectedSystem.id} rackId={rackId!} onClose={() => setSelectedSystem(null)} />}
      </div>
    </PageShell>
  );
}
