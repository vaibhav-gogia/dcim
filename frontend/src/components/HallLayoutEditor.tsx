import { useState } from "react";
import { useMutation, useQueryClient } from "@tanstack/react-query";
import { api } from "../api/client";
import { FloorRack } from "../api/types";
import DataCenterFloorView from "./DataCenterFloorView";
import { InventoryButton } from "./InventoryEditor";
import { colors, space } from "../theme";

export default function HallLayoutEditor({ hallId, racks, onClose }: { hallId: string; racks: FloorRack[]; onClose: () => void }) {
  const [original] = useState(() => racks.map(r => ({ ...r })));
  const [draft, setDraft] = useState(original);
  const client = useQueryClient();
  const overlapping = draft.some((a, i) => draft.slice(i + 1).some(b => Math.abs(a.pos_x - b.pos_x) < 0.75 && Math.abs(a.pos_y - b.pos_y) < 0.55));
  const changed = draft.some((r, i) => r.pos_x !== original[i].pos_x || r.pos_y !== original[i].pos_y);
  const save = useMutation({ mutationFn: () => api.patch(`/data-halls/${hallId}/layout`, { racks: draft.map((r, i) => ({ id: r.id, pos_x: r.pos_x, pos_y: r.pos_y, previous_x: original[i].pos_x, previous_y: original[i].pos_y })) }),
    onSuccess: async () => { await client.invalidateQueries(); onClose(); } });
  return <section aria-label="Edit hall layout">
    <p>Drag racks to reposition them, or focus a rack and use the arrow keys. Positions snap to tenths of a cell. Changes apply only after saving.</p>
    <div style={{ display: "flex", gap: space.sm, marginBottom: space.md }}>
      <InventoryButton disabled={save.isPending || overlapping || !changed} onClick={() => save.mutate()}>{save.isPending ? "Saving…" : "Save layout"}</InventoryButton>
      <InventoryButton disabled={save.isPending} onClick={onClose}>Cancel</InventoryButton>
    </div>
    {overlapping && <p role="alert" style={{ color: colors.statusCritical }}>Rack positions overlap. Move them apart before saving.</p>}
    {save.error && <p role="alert" style={{ color: colors.statusCritical }}>{save.error.message}</p>}
    <DataCenterFloorView racks={draft} disabled={save.isPending} onMove={(id, x, y) => { save.reset(); setDraft(previous => previous.map(r => r.id === id ? { ...r, pos_x: x, pos_y: y } : r)); }} />
  </section>;
}
