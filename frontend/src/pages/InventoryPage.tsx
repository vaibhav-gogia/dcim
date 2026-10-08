import { useEffect, useState } from "react";
import { Link, useSearchParams } from "react-router-dom";
import { useQuery } from "@tanstack/react-query";
import { api } from "../api/client";
import { useDataCenters } from "../api/hooks";
import { PowerState } from "../api/types";
import PageShell from "../components/PageShell";
import StatusBadge from "../components/StatusBadge";
import { InventoryButton } from "../components/InventoryEditor";
import { colors, fontSize, radius, space } from "../theme";

interface SearchItem {
  id: string; name: string; serial_number: string | null; manufacturer: string | null; model: string | null;
  system_type: string; power_state: PowerState; rack_id: string; rack_name: string;
  data_hall_name: string; datacenter_name: string;
}
interface Filters { manufacturers: string[]; system_types: string[]; data_halls: { id: string; name: string; datacenter_id: string }[] }
const states: PowerState[] = ["unknown", "off", "booting", "on", "shutting_down", "cycling"];

export default function InventoryPage() {
  const [params, setParams] = useSearchParams();
  const [draft, setDraft] = useState(params.get("q") ?? "");
  const currentQuery = params.get("q") ?? "";
  useEffect(() => setDraft(currentQuery), [currentQuery]);
  const offset = Math.max(0, Number(params.get("offset")) || 0);
  const requestParams = new URLSearchParams();
  for (const key of ["q", "datacenter_id", "data_hall_id", "manufacturer", "system_type", "power_state"]) {
    const value = params.get(key); if (value) requestParams.set(key, value);
  }
  requestParams.set("offset", String(offset));
  requestParams.set("limit", "25");
  const result = useQuery({ queryKey: ["inventory", requestParams.toString()], queryFn: () => api.get<{ items: SearchItem[]; total: number }>(`/inventory/systems?${requestParams}`), refetchInterval: 5000 });
  const filters = useQuery({ queryKey: ["inventory-filters"], queryFn: () => api.get<Filters>("/inventory/filters") });
  const centers = useDataCenters();
  function change(key: string, value: string) {
    setParams(previous => { const next = new URLSearchParams(previous); if (value) next.set(key, value); else next.delete(key); next.delete("offset"); if (key === "datacenter_id") next.delete("data_hall_id"); return next; });
  }
  const style = { padding: space.sm, fontSize: fontSize.sm, border: `1px solid ${colors.border}`, borderRadius: radius.sm, background: colors.surface0, color: colors.textPrimary, minWidth: 0 };
  const hallOptions = filters.data?.data_halls.filter(h => !params.get("datacenter_id") || h.datacenter_id === params.get("datacenter_id")) ?? [];
  const filterError = filters.error ?? centers.error;
  function dropdown(key: string, label: string, options: { value: string; label: string }[]) {
    return <label style={{ display: "grid", gap: space.xs }}>{label}<select style={style} value={params.get(key) ?? ""} onChange={e => change(key, e.target.value)}>
      <option value="">All</option>{options.map(o => <option key={o.value} value={o.value}>{o.label}</option>)}
    </select></label>;
  }
  return <PageShell crumbs={[{ label: "Data Centers", to: "/" }, { label: "Inventory" }]} title="Search inventory">
    <p style={{ color: colors.textMuted }}>Find systems by name, serial number, manufacturer, model, or location.</p>
    <section aria-label="Inventory filters" style={{ padding: space.lg, background: colors.surface1, border: `1px solid ${colors.border}`, borderRadius: radius.md, marginBottom: space.lg }}>
      <form onSubmit={e => { e.preventDefault(); change("q", draft.trim()); }} style={{ display: "flex", gap: space.sm, flexWrap: "wrap", marginBottom: space.md }}>
        <label style={{ display: "grid", gap: space.xs, flex: "1 1 240px" }}>Search systems<input type="search" maxLength={200} style={style} value={draft} onChange={e => setDraft(e.target.value)} placeholder="e.g. serial number, Dell, Hall 1…" /></label>
        <InventoryButton type="submit" style={{ alignSelf: "end" }}>Search</InventoryButton>
        <InventoryButton type="button" style={{ alignSelf: "end" }} onClick={() => { setDraft(""); setParams({}); }}>Clear filters</InventoryButton>
      </form>
      <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(170px, 1fr))", gap: space.md }}>
        {dropdown("datacenter_id", "Data center", centers.data?.map(d => ({ value: d.id, label: d.name })) ?? [])}
        {dropdown("data_hall_id", "Data hall", hallOptions.map(h => ({ value: h.id, label: `${centers.data?.find(d => d.id === h.datacenter_id)?.name ?? "DC"} / ${h.name}` })))}
        {dropdown("manufacturer", "Manufacturer", filters.data?.manufacturers.map(m => ({ value: m, label: m })) ?? [])}
        {dropdown("system_type", "System type", filters.data?.system_types.map(t => ({ value: t, label: t })) ?? [])}
        {dropdown("power_state", "Power state", states.map(s => ({ value: s, label: s.replace(/_/g, " ") })))}
      </div>
      {filterError && <p role="alert">Unable to load filter options: {filterError.message}</p>}
    </section>
    {result.isPending ? <p role="status">Searching inventory…</p> : result.error ? <p role="alert">{result.error.message} <InventoryButton onClick={() => result.refetch()}>Retry</InventoryButton></p> : result.data && <>
      <p role="status">{result.data.total} matching system{result.data.total === 1 ? "" : "s"}{result.isFetching ? " · Updating…" : ""}</p>
      {!result.data.items.length ? <p>No systems match these filters. Try a broader search or clear the filters.</p> : <div style={{ overflowX: "auto", background: colors.surface1, border: `1px solid ${colors.border}`, borderRadius: radius.md }}>
        <table style={{ width: "100%", textAlign: "left", fontSize: fontSize.sm }}>
          <caption style={{ textAlign: "left", padding: space.md, color: colors.textMuted }}>Systems {offset + 1}–{offset + result.data.items.length} of {result.data.total}</caption>
          <thead><tr>{["System", "Manufacturer / model", "Serial number", "Location", "Type", "Power"].map(h => <th key={h} scope="col" style={{ padding: space.md, borderBottom: `1px solid ${colors.border}` }}>{h}</th>)}</tr></thead>
          <tbody>{result.data.items.map(s => <tr key={s.id}>
            <td style={{ padding: space.md }}><Link to={`/rack/${s.rack_id}?system=${s.id}`}>{s.name}</Link></td>
            <td style={{ padding: space.md }}>{[s.manufacturer, s.model].filter(Boolean).join(" / ") || "—"}</td>
            <td style={{ padding: space.md }}>{s.serial_number ?? "—"}</td>
            <td style={{ padding: space.md }}>{s.datacenter_name} / {s.data_hall_name} / {s.rack_name}</td>
            <td style={{ padding: space.md }}>{s.system_type}</td>
            <td style={{ padding: space.md }}><StatusBadge state={s.power_state} /></td>
          </tr>)}</tbody>
        </table>
      </div>}
      <div style={{ display: "flex", gap: space.sm, marginTop: space.md }}>
        <InventoryButton disabled={!offset} onClick={() => setParams(p => { const next = new URLSearchParams(p); next.set("offset", String(Math.max(0, offset - 25))); return next; })}>Previous</InventoryButton>
        <InventoryButton disabled={offset + 25 >= result.data.total} onClick={() => setParams(p => { const next = new URLSearchParams(p); next.set("offset", String(offset + 25)); return next; })}>Next</InventoryButton>
      </div>
    </>}
  </PageShell>;
}
