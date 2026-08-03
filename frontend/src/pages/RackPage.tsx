import { useState } from "react";
import { Link, useParams } from "react-router-dom";

import { useRackElevation } from "../api/hooks";
import { SystemElevation } from "../api/types";
import PduPanel from "../components/PduPanel";
import RackElevation from "../components/RackElevation";
import SystemDetailPanel from "../components/SystemDetailPanel";

export default function RackPage() {
  const { rackId } = useParams<{ rackId: string }>();
  const { data: rack, isLoading } = useRackElevation(rackId!);
  const [selectedSystem, setSelectedSystem] = useState<SystemElevation | null>(null);

  if (isLoading || !rack) return <div style={{ padding: 24 }}>Loading...</div>;

  return (
    <div style={{ padding: 24 }}>
      <Link to="/">← Data Centers</Link>
      <h1>{rack.name}</h1>
      <div style={{ display: "flex", gap: 24, alignItems: "flex-start" }}>
        <RackElevation
          rack={rack}
          selectedSystemId={selectedSystem?.id ?? null}
          onSelectSystem={setSelectedSystem}
        />
        <PduPanel rackId={rackId!} />
        {selectedSystem && (
          <SystemDetailPanel
            systemId={selectedSystem.id}
            rackId={rackId!}
            onClose={() => setSelectedSystem(null)}
          />
        )}
      </div>
    </div>
  );
}
