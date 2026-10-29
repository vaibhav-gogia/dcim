import { useState } from "react";

import { RackElevation as RackElevationData, SystemElevation } from "../api/types";
import { colors, radius } from "../theme";
import { isTransient, POWER_STATUS } from "./statusTokens";

// Font sizes here are deliberately literal, not from the shared theme.fontSize scale:
// this rack elevation's proportions are locked in as-is, independent of app-wide type-scale changes.
const TEXT_MICRO = 10;
const TEXT_XS = 12;
const TEXT_SM = 13;

const U_HEIGHT_PX = 14; // Compact physical scale; a 3U division is 42px tall.
const DIVISION_U = 3;
const RACK_WIDTH_PX = 300;
const TICK_MARGIN_PX = 44;

export default function RackElevation({
  rack,
  selectedSystemId,
  onSelectSystem,
}: {
  rack: RackElevationData;
  selectedSystemId: string | null;
  onSelectSystem: (system: SystemElevation) => void;
}) {
  const [hoveredId, setHoveredId] = useState<string | null>(null);

  // Show every physical U, including all unused capacity above the equipment.
  const visibleUHeight = rack.u_height;
  const occupied = new Set<number>();
  for (const system of rack.systems) {
    for (let u = system.u_position; u < system.u_position + system.u_height; u++) {
      if (u >= 1 && u <= rack.u_height) occupied.add(u);
    }
  }
  const openUnits = rack.u_height - occupied.size;

  const totalHeight = visibleUHeight * U_HEIGHT_PX;
  const frameWidth = RACK_WIDTH_PX;
  const svgWidth = TICK_MARGIN_PX + frameWidth;
  const topLabelHeight = 54;

  const units = Array.from({ length: visibleUHeight }, (_, i) => i + 1);
  const divisions = Array.from({ length: Math.ceil(visibleUHeight / DIVISION_U) }, (_, i) => {
    const bottom = i * DIVISION_U + 1;
    return { bottom, top: Math.min(bottom + DIVISION_U - 1, visibleUHeight) };
  });
  const openRanges: { bottom: number; top: number }[] = [];
  for (const u of units) {
    if (occupied.has(u)) continue;
    const previous = openRanges[openRanges.length - 1];
    if (previous && previous.top === u - 1) previous.top = u;
    else openRanges.push({ bottom: u, top: u });
  }

  return (
    <svg aria-label={`${rack.name}: ${rack.u_height}U, ${occupied.size} occupied, ${openUnits} open`} width={svgWidth} height={totalHeight + topLabelHeight + 10} viewBox={`0 0 ${svgWidth} ${totalHeight + topLabelHeight + 10}`}>
      <text x={TICK_MARGIN_PX} y={12} fontSize={TEXT_XS} fill={colors.textMuted}>
        {rack.systems.length} system{rack.systems.length === 1 ? "" : "s"} · {rack.u_height}U rack
      </text>

      <text x={TICK_MARGIN_PX} y={28} fontSize={TEXT_XS} fill={colors.textSecondary}>
        {occupied.size}U occupied · {openUnits}U open
      </text>

      <text x={TICK_MARGIN_PX} y={44} fontSize={TEXT_MICRO} fill={colors.textMuted}>
        Major divisions: 3U · thin lines: 1U
      </text>

      <rect
        x={TICK_MARGIN_PX}
        y={topLabelHeight}
        width={frameWidth}
        height={totalHeight}
        rx={radius.sm}
        fill={colors.surface1}
        stroke={colors.border}
      />

      {units.filter(u => !occupied.has(u)).map(u => {
        const y = topLabelHeight + (visibleUHeight - u) * U_HEIGHT_PX;
        return <g key={`open-${u}`}>
          <title>U{u}: open</title>
          <rect x={TICK_MARGIN_PX + 4} y={y + 1} width={frameWidth - 8} height={U_HEIGHT_PX - 2} fill={colors.surface0} />
        </g>;
      })}

      {/* Every label denotes a physical U range, not a fixed equipment slot. */}
      {divisions.map(({ bottom, top }) => {
        const y = topLabelHeight + (visibleUHeight - top) * U_HEIGHT_PX;
        const height = (top - bottom + 1) * U_HEIGHT_PX;
        return <text key={`division-${bottom}`} x={TICK_MARGIN_PX - 6} y={y + height / 2 + 3} textAnchor="end" fontSize={TEXT_MICRO} fill={colors.textMuted}>
          {bottom === top ? top : `${bottom}–${top}`}
        </text>;
      })}

      {openRanges.map(({ bottom, top }) => {
        const height = (top - bottom + 1) * U_HEIGHT_PX;
        const y = topLabelHeight + (visibleUHeight - top) * U_HEIGHT_PX;
        return <text key={`open-label-${bottom}`} x={TICK_MARGIN_PX + frameWidth / 2} y={y + height / 2 + 3} textAnchor="middle" fontSize={TEXT_MICRO} fill={colors.textMuted}>
          Open · {top - bottom + 1}U
        </text>;
      })}

      {Array.from({ length: visibleUHeight + 1 }, (_, i) => {
        const y = topLabelHeight + i * U_HEIGHT_PX;
        const major = i === 0 || (visibleUHeight - i) % DIVISION_U === 0;
        return <line key={`hairline-${i}`} x1={TICK_MARGIN_PX} y1={y} x2={svgWidth} y2={y} stroke={major ? colors.border : colors.gridline} strokeWidth={major ? 1.5 : 0.5} opacity={major ? 1 : 0.55} />;
      })}

      {rack.systems.map((system) => {
        const topU = system.u_position + system.u_height - 1;
        const y = topLabelHeight + (visibleUHeight - topU) * U_HEIGHT_PX;
        const height = system.u_height * U_HEIGHT_PX;
        const token = POWER_STATUS[system.power_state];
        const isSelected = system.id === selectedSystemId;
        const isHovered = system.id === hoveredId;

        return (
          <g
            key={system.id}
            role="button"
            tabIndex={0}
            aria-label={`${system.name}, U${system.u_position}–U${topU}, ${system.power_state}`}
            onKeyDown={event => { if (event.key === "Enter" || event.key === " ") { event.preventDefault(); onSelectSystem(system); } }}
            onClick={() => onSelectSystem(system)}
            onMouseEnter={() => setHoveredId(system.id)}
            onMouseLeave={() => setHoveredId(null)}
            style={{ cursor: "pointer" }}
          >
            <title>{system.name}: U{system.u_position}–U{topU}</title>
            <rect
              x={TICK_MARGIN_PX + 4}
              y={y + 1}
              width={frameWidth - 8}
              height={height - 2}
              rx={radius.sm}
              fill={isHovered ? colors.surface2 : colors.surface1}
              stroke={isSelected ? colors.accent : colors.border}
              strokeWidth={isSelected ? 2 : 1}
            />
            {/* left accent bar carries the status color; block fill stays neutral */}
            <rect x={TICK_MARGIN_PX + 4} y={y + 1} width={4} height={height - 2} fill={token.color} />
            <text x={TICK_MARGIN_PX + 16} y={y + height / 2 + (system.u_height === 1 ? 3 : 4)} fontSize={system.u_height === 1 ? TEXT_MICRO : TEXT_SM} fill={colors.textPrimary}>
              {system.name}
            </text>
            <text
              x={TICK_MARGIN_PX + frameWidth - 12}
              y={y + height / 2 + (system.u_height === 1 ? 3 : 4)}
              textAnchor="end"
              fontSize={system.u_height === 1 ? TEXT_MICRO : TEXT_SM}
              fill={token.color}
              opacity={isTransient(system.power_state) ? 0.9 : 1}
            >
              {token.glyph}
            </text>
          </g>
        );
      })}
    </svg>
  );
}
