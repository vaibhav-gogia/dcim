import { useState, FormEvent, ButtonHTMLAttributes } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { api } from "../api/client";
import { colors, fontSize, radius, space } from "../theme";

interface Field { key: string; label: string; type?: "number"; min?: number; step?: number; required?: boolean; defaultValue?: string | number }
export const dataCenterFields: Field[] = [
  { key: "name", label: "Name", required: true }, { key: "location", label: "Location" },
];
export const dataHallFields: Field[] = [{ key: "name", label: "Name", required: true }];
export const rackFields: Field[] = [
  { key: "name", label: "Name", required: true },
  { key: "u_height", label: "Capacity (U)", type: "number", min: 1, defaultValue: 42 },
  { key: "pos_x", label: "Floor column", type: "number", step: 0.1, min: 0, defaultValue: 0 },
  { key: "pos_y", label: "Floor row", type: "number", step: 0.1, min: 0, defaultValue: 0 },
];
export const pduFields: Field[] = [
  { key: "name", label: "Name", required: true },
  { key: "outlet_count", label: "Number of outlets (1–96)", type: "number", min: 1, defaultValue: 24 },
];
export const pduEditFields: Field[] = [{ key: "name", label: "Name", required: true }];
export const systemFields: Field[] = [
  { key: "name", label: "Name", required: true },
  { key: "u_position", label: "Starting U", type: "number", min: 1, defaultValue: 1 },
  { key: "u_height", label: "Height (U)", type: "number", min: 1, defaultValue: 3 },
  { key: "system_type", label: "System type", required: true, defaultValue: "server" },
  { key: "manufacturer", label: "Manufacturer" }, { key: "model", label: "Model" },
  { key: "serial_number", label: "Serial number" },
];

export function InventoryButton(props: ButtonHTMLAttributes<HTMLButtonElement>) {
  return <button {...props} style={{ padding: "9px 18px", border: `1px solid ${colors.border}`, borderRadius: radius.sm,
    background: colors.surface2, color: colors.textPrimary, fontSize: fontSize.sm, cursor: props.disabled ? "wait" : "pointer", ...props.style }} />;
}

interface Props { title: string; path: string; editing?: boolean; fields: Field[]; onClose: () => void }
export default function InventoryEditor(props: Props) {
  const initial = useQuery({ queryKey: ["inventory-edit", props.path], queryFn: () => api.get<Record<string, unknown>>(props.path), enabled: !!props.editing, staleTime: 0 });
  if (props.editing && initial.isPending) return <p role="status">Loading details…</p>;
  if (props.editing && initial.isError) return <div role="alert">{initial.error.message} <InventoryButton onClick={() => initial.refetch()}>Retry</InventoryButton> <InventoryButton onClick={props.onClose}>Cancel</InventoryButton></div>;
  return <EditorForm {...props} initial={props.editing ? initial.data : undefined} />;
}

function EditorForm({ title, path, editing, fields, onClose, initial }: Props & { initial?: Record<string, unknown> }) {
  const [values, setValues] = useState<Record<string, string>>(() => Object.fromEntries(fields.map(f => [f.key, String(initial?.[f.key] ?? f.defaultValue ?? "")])));
  const client = useQueryClient();
  const save = useMutation({
    mutationFn: () => {
      const body = Object.fromEntries(fields.map(f => [f.key, f.type === "number" ? Number(values[f.key]) : values[f.key].trim() || null]));
      return editing ? api.patch(path, body) : api.post(path, body);
    },
    onSuccess: async () => { await client.invalidateQueries(); onClose(); },
  });
  function submit(event: FormEvent) { event.preventDefault(); save.mutate(); }
  return <form onSubmit={submit} aria-label={title} style={{ background: colors.surface1, border: `1px solid ${colors.border}`, borderRadius: radius.md, padding: space.lg, marginBottom: space.lg, maxWidth: 720 }}>
    <h2 style={{ marginTop: 0, fontSize: fontSize.xl }}>{title}</h2>
    <fieldset disabled={save.isPending} style={{ border: 0, padding: 0, margin: 0 }}>
      <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(200px, 1fr))", gap: space.md }}>
        {fields.map(f => <label key={f.key} style={{ display: "flex", flexDirection: "column", gap: space.xs }}>
          {f.label}
          <input autoFocus={f === fields[0]} required={f.required || f.type === "number"} type={f.type ?? "text"} min={f.min} step={f.step ?? 1}
            value={values[f.key]} onChange={e => setValues(v => ({ ...v, [f.key]: e.target.value }))}
            pattern={f.type ? undefined : f.required ? ".*\\S.*" : undefined}
            style={{ padding: space.sm, fontSize: fontSize.md, borderRadius: radius.sm, border: `1px solid ${colors.border}`, background: colors.surface0, color: colors.textPrimary, minWidth: 0 }} />
        </label>)}
      </div>
      {save.isError && <p role="alert" style={{ color: colors.statusCritical }}>{save.error.message}</p>}
      <div style={{ display: "flex", gap: space.sm, marginTop: space.lg }}>
        <InventoryButton type="submit">{save.isPending ? "Saving…" : "Save"}</InventoryButton>
        <InventoryButton type="button" onClick={onClose}>Cancel</InventoryButton>
      </div>
    </fieldset>
  </form>;
}
