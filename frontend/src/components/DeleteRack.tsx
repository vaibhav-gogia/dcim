import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { api } from "../api/client";
import { InventoryButton } from "./InventoryEditor";
import { colors, radius, space } from "../theme";

export default function DeleteRack({ rackId, name, hallId, onClose }: { rackId: string; name: string; hallId: string; onClose: () => void }) {
  const [confirmation, setConfirmation] = useState("");
  const client = useQueryClient();
  const navigate = useNavigate();
  const summary = useQuery({ queryKey: ["rack-deletion-summary", rackId], queryFn: () => api.get<{ systems: number; pdus: number; outlets: number; connections: number }>(`/racks/${rackId}/deletion-summary`), staleTime: 0 });
  const remove = useMutation({ mutationFn: () => api.delete(`/racks/${rackId}`), onSuccess: () => {
    client.removeQueries({ queryKey: ["rack-elevation", rackId] });
    client.invalidateQueries();
    navigate(`/hall/${hallId}`, { replace: true });
  } });
  return <section role="dialog" aria-labelledby="delete-rack-title" style={{ padding: space.lg, marginBottom: space.lg, maxWidth: 720, border: `1px solid ${colors.statusCritical}`, background: colors.surface1, borderRadius: radius.md }}>
    <h2 id="delete-rack-title" style={{ marginTop: 0 }}>Delete {name}?</h2>
    <p>This permanently removes the rack and its inventory records. It cannot be undone. This does not send power commands to equipment.</p>
    {summary.isPending && <p role="status">Checking rack contents…</p>}
    {summary.error && <p role="alert">{summary.error.message} <InventoryButton onClick={() => summary.refetch()}>Retry</InventoryButton></p>}
    {summary.data && <p>Also removed: <strong>{summary.data.systems} systems, {summary.data.pdus} PDUs, {summary.data.outlets} outlets, and {summary.data.connections} power connections</strong>.</p>}
    <form onSubmit={event => { event.preventDefault(); if (summary.data && confirmation === name && !remove.isPending) remove.mutate(); }}>
      <label style={{ display: "grid", gap: space.sm }}>Type the rack name to confirm: <strong>{name}</strong>
        <input autoFocus value={confirmation} disabled={remove.isPending} onChange={e => setConfirmation(e.target.value)} autoComplete="off" style={{ padding: space.sm, background: colors.surface0, color: colors.textPrimary, border: `1px solid ${colors.border}`, borderRadius: radius.sm }} />
      </label>
      {remove.error && <p role="alert" style={{ color: colors.statusCritical }}>{remove.error.message}</p>}
      <div style={{ display: "flex", gap: space.sm, marginTop: space.md }}>
        <InventoryButton type="submit" disabled={!summary.data || summary.isFetching || confirmation !== name || remove.isPending} style={{ color: colors.statusCritical }}>{remove.isPending ? "Deleting…" : "Permanently delete rack"}</InventoryButton>
        <InventoryButton type="button" disabled={remove.isPending} onClick={onClose}>Cancel</InventoryButton>
      </div>
    </form>
  </section>;
}
