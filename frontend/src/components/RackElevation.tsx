import { useState } from "react";

import { RackElevation as RackElevationData, SystemElevation } from "../api/types";
import { colors, radius } from "../theme";
import { isTransient, POWER_STATUS } from "./statusTokens";

// Font sizes here are deliberately literal, not from the shared theme.fontSize scale:
// this rack elevation's proportions are locked in as-is, independent of app-wide type-scale changes.
const TEXT_MICRO = 10;
const TEXT_XS = 12;
const TEXT_SM = 13;

const U_HEIGHT_PX = 21; // bumped from 18 so 1U rows comfortably fit the larger system-name text
const RACK_WIDTH_PX = 300;
const TICK_MARGIN_PX = 26;
const TICK_INTERVAL = 5;
const TOP_HEADROOM_U = 3; // a little empty rail above the highest system, like real spare capacity
const MIN_VISIBLE_U = 10; // never render a frame so short it looks broken for near-empty racks

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

  // Render only as much of the rack as is actually populated (+ headroom) instead of
  // always the full physical U height — a rack using 8 of 42U otherwise renders as a
  // mostly-empty column, which doesn't read as a real, in-use rack.
  const highestOccupiedU = rack.systems.reduce((max, s) => Math.max(max, s.u_position + s.u_height - 1), 0);
  const visibleUHeight = Math.min(rack.u_height, Math.max(MIN_VISIBLE_U, highestOccupiedU + TOP_HEADROOM_U));

  const totalHeight = visibleUHeight * U_HEIGHT_PX;
  const frameWidth = RACK_WIDTH_PX;
  const svgWidth = TICK_MARGIN_PX + frameWidth;
  const topLabelHeight = 20;

  const ticks: number[] = [];
  for (let u = TICK_INTERVAL; u <= visibleUHeight; u += TICK_INTERVAL) {
    ticks.push(u);
  }

  return (
    <svg width={svgWidth} height={totalHeight + topLabelHeight + 10} viewBox={`0 0 ${svgWidth} ${totalHeight + topLabelHeight + 10}`}>
      <text x={TICK_MARGIN_PX} y={12} fontSize={TEXT_XS} fill={colors.textMuted}>
        {rack.systems.length} system{rack.systems.length === 1 ? "" : "s"} · {rack.u_height}U rack
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

      {/* U-position tick marks + labels on empty rail space */}
      {ticks.map((u) => {
        const yFromTop = visibleUHeight - u + 1;
        const y = topLabelHeight + (yFromTop - 1) * U_HEIGHT_PX;
        return (
          <text key={`tick-${u}`} x={TICK_MARGIN_PX - 6} y={y + U_HEIGHT_PX / 2 + 3} textAnchor="end" fontSize={TEXT_MICRO} fill={colors.textMuted}>
            {u}
          </text>
        );
      })}

      {/* Hairlines at every U boundary in empty rail space, so the rack reads as a rack */}
      {Array.from({ length: visibleUHeight + 1 }, (_, i) => i).map((i) => {
        const y = topLabelHeight + i * U_HEIGHT_PX;
        return <line key={`hairline-${i}`} x1={TICK_MARGIN_PX} y1={y} x2={svgWidth} y2={y} stroke={colors.gridline} strokeWidth={1} />;
      })}

      {rack.systems.map((system) => {
        const yFromTop = visibleUHeight - system.u_position - system.u_height + 1;
        const y = topLabelHeight + (yFromTop - 1) * U_HEIGHT_PX;
        const height = system.u_height * U_HEIGHT_PX;
        const token = POWER_STATUS[system.power_state];
        const isSelected = system.id === selectedSystemId;
        const isHovered = system.id === hoveredId;

        return (
          <g
            key={system.id}
            onClick={() => onSelectSystem(system)}
            onMouseEnter={() => setHoveredId(system.id)}
            onMouseLeave={() => setHoveredId(null)}
            style={{ cursor: "pointer" }}
          >
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
            <text x={TICK_MARGIN_PX + 16} y={y + height / 2 + 4} fontSize={TEXT_SM} fill={colors.textPrimary}>
              {system.name}
            </text>
            <text
              x={TICK_MARGIN_PX + frameWidth - 12}
              y={y + height / 2 + 4}
              textAnchor="end"
              fontSize={TEXT_SM}
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
