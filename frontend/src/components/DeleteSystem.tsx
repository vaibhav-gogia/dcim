import { useState } from "react";
import { useMutation, useQueryClient } from "@tanstack/react-query";
import { api } from "../api/client";
import { InventoryButton } from "./InventoryEditor";
import { colors, radius, space } from "../theme";

export default function DeleteSystem({ systemId, name, onDeleted, onCancel }: { systemId: string; name: string; onDeleted: () => void; onCancel: () => void }) {
  const [confirmation, setConfirmation] = useState("");
  const client = useQueryClient();
  const remove = useMutation({ mutationFn: () => api.delete(`/systems/${systemId}`), onSuccess: async () => {
    onDeleted();
    for (const key of ["system", "system-health", "power-connections"]) {
      await client.cancelQueries({ queryKey: [key, systemId] });
      client.removeQueries({ queryKey: [key, systemId] });
    }
    await client.invalidateQueries();
  } });
  return <section role="dialog" aria-labelledby="delete-system-title" style={{ padding: space.md, marginTop: space.md, border: `1px solid ${colors.statusCritical}`, borderRadius: radius.sm }}>
    <h4 id="delete-system-title" style={{ margin: `0 0 ${space.sm}px` }}>Delete {name}?</h4>
    <p>This permanently removes this system and its PSU wiring records. Its rack, PDUs, and action history are kept. This cannot be undone.</p>
    <p>Deleting inventory does not power off equipment or change outlet power.</p>
    <form onSubmit={event => { event.preventDefault(); if (confirmation === name && !remove.isPending) remove.mutate(); }}>
      <label style={{ display: "grid", gap: space.sm }}>Type the exact system name to confirm: <strong>{name}</strong>
        <input autoFocus autoComplete="off" value={confirmation} disabled={remove.isPending} onChange={e => setConfirmation(e.target.value)} style={{ minWidth: 0, width: "100%", padding: space.sm, fontSize: 16, background: colors.surface0, color: colors.textPrimary, border: `1px solid ${colors.border}`, borderRadius: radius.sm }} />
      </label>
      {remove.error && <p role="alert" style={{ color: colors.statusCritical }}>{remove.error.message}</p>}
      <div style={{ display: "flex", flexWrap: "wrap", gap: space.sm, marginTop: space.md }}>
        <InventoryButton type="submit" disabled={confirmation !== name || remove.isPending} style={{ color: colors.statusCritical }}>{remove.isPending ? "Deleting…" : "Permanently delete system"}</InventoryButton>
        <InventoryButton type="button" disabled={remove.isPending} onClick={onCancel}>Cancel</InventoryButton>
      </div>
    </form>
  </section>;
}
