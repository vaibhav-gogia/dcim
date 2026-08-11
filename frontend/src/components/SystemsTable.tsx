import { useMemo, useState } from "react";

import { SystemElevation } from "../api/types";
import { colors, fontSize, space } from "../theme";
import StatusBadge from "./StatusBadge";

type SortKey = "name" | "system_type" | "u_position" | "power_state";

function sortValue(system: SystemElevation, key: SortKey): string | number {
  return key === "u_position" ? system.u_position : system[key];
}

export default function SystemsTable({
  systems,
  selectedSystemId,
  onSelectSystem,
}: {
  systems: SystemElevation[];
  selectedSystemId: string | null;
  onSelectSystem: (system: SystemElevation) => void;
}) {
  const [sortKey, setSortKey] = useState<SortKey>("u_position");
  const [ascending, setAscending] = useState(true);

  const sorted = useMemo(() => {
    const copy = [...systems];
    copy.sort((a, b) => {
      const av = sortValue(a, sortKey);
      const bv = sortValue(b, sortKey);
      const cmp = av < bv ? -1 : av > bv ? 1 : 0;
      return ascending ? cmp : -cmp;
    });
    return copy;
  }, [systems, sortKey, ascending]);

  function toggleSort(key: SortKey) {
    if (key === sortKey) {
      setAscending((prev) => !prev);
    } else {
      setSortKey(key);
      setAscending(true);
    }
  }

  const columns: { key: SortKey; label: string }[] = [
    { key: "name", label: "Name" },
    { key: "system_type", label: "Type" },
    { key: "u_position", label: "U Position" },
    { key: "power_state", label: "State" },
  ];

  return (
    <table style={{ width: "100%", maxWidth: 720, fontSize: fontSize.sm }}>
      <thead>
        <tr>
          {columns.map((col) => (
            <th
              key={col.key}
              onClick={() => toggleSort(col.key)}
              style={{
                textAlign: "left",
                padding: `${space.xs}px ${space.sm}px`,
                borderBottom: `1px solid ${colors.border}`,
                color: colors.textMuted,
                fontWeight: 600,
                cursor: "pointer",
                userSelect: "none",
              }}
            >
              {col.label}
              {sortKey === col.key ? (ascending ? " ▲" : " ▼") : ""}
            </th>
          ))}
        </tr>
      </thead>
      <tbody>
        {sorted.map((system) => {
          const isSelected = system.id === selectedSystemId;
          return (
            <tr
              key={system.id}
              onClick={() => onSelectSystem(system)}
              style={{
                cursor: "pointer",
                background: isSelected ? colors.surface2 : "transparent",
              }}
            >
              <td style={{ padding: `${space.xs}px ${space.sm}px`, borderBottom: `1px solid ${colors.gridline}`, color: colors.textPrimary }}>
                {system.name}
              </td>
              <td style={{ padding: `${space.xs}px ${space.sm}px`, borderBottom: `1px solid ${colors.gridline}`, color: colors.textSecondary }}>
                {system.system_type}
              </td>
              <td
                style={{
                  padding: `${space.xs}px ${space.sm}px`,
                  borderBottom: `1px solid ${colors.gridline}`,
                  color: colors.textSecondary,
                  fontVariantNumeric: "tabular-nums",
                }}
              >
                U{system.u_position}-{system.u_position + system.u_height - 1}
              </td>
              <td style={{ padding: `${space.xs}px ${space.sm}px`, borderBottom: `1px solid ${colors.gridline}` }}>
                <StatusBadge state={system.power_state} size="sm" />
              </td>
            </tr>
          );
        })}
      </tbody>
    </table>
  );
}
