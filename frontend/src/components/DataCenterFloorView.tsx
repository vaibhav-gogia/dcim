import { useState, PointerEvent } from "react";
import { useNavigate } from "react-router-dom";

import { FloorRack } from "../api/types";
import { colors, fontSize, radius } from "../theme";

const CELL_SIZE = 200; //grid spacing between racks
const RACK_WIDTH = 150; //rack tile width
const RACK_DEPTH = 110; //rack tile depth
const DOT_SPACING = 4; //floor dot-grid spacing

export default function DataCenterFloorView({ racks, onMove, disabled = false }: { racks: FloorRack[]; onMove?: (id: string, x: number, y: number) => void; disabled?: boolean }) {
  const navigate = useNavigate();
  const [hoveredId, setHoveredId] = useState<string | null>(null);

  const [drag, setDrag] = useState<{ id: string; startX: number; startY: number; x: number; y: number } | null>(null);
  function point(event: PointerEvent<SVGGElement>) {
    const svg = event.currentTarget.ownerSVGElement!;
    const matrix = svg.getScreenCTM();
    return matrix ? new DOMPoint(event.clientX, event.clientY).matrixTransform(matrix.inverse()) : new DOMPoint();
  }
  const maxX = Math.max(1, ...racks.map((r) => r.pos_x));
  const maxY = Math.max(1, ...racks.map((r) => r.pos_y));
  const width = (maxX + (onMove ? 3 : 1)) * CELL_SIZE;
  const height = (maxY + (onMove ? 3 : 1)) * CELL_SIZE;

  return (
    <svg
      width="100%"
      viewBox={`0 0 ${width} ${height}`}
      style={{ maxWidth: width, touchAction: onMove ? "none" : undefined, borderRadius: radius.md, border: `1px solid ${colors.border}` }}
    >
      <defs>
        <pattern id="floor-dots" width={DOT_SPACING} height={DOT_SPACING} patternUnits="userSpaceOnUse">
          <circle cx={1} cy={1} r={1} fill={colors.gridline} />
        </pattern>
      </defs>
      <rect width={width} height={height} fill={colors.surface0} />
      <rect width={width} height={height} fill="url(#floor-dots)" />

      {racks.map((rack) => {
        const x = drag?.id === rack.id ? drag.x : rack.pos_x;
        const y = drag?.id === rack.id ? drag.y : rack.pos_y;
        const isHovered = rack.id === hoveredId;
        return (
          <g
            key={rack.id}
            transform={`translate(${x * CELL_SIZE + 16}, ${y * CELL_SIZE + 16})`}
            role="button"
            tabIndex={disabled ? -1 : 0}
            aria-label={onMove ? `${rack.name}, column ${x}, row ${y}. Use arrow keys to move.` : `Open ${rack.name}`}
            onClick={() => { if (!onMove) navigate(`/rack/${rack.id}`); }}
            onKeyDown={event => {
              if (!onMove) { if (event.key === "Enter" || event.key === " ") { event.preventDefault(); navigate(`/rack/${rack.id}`); } return; }
              if (disabled) return;
              const delta: Record<string, [number, number]> = { ArrowLeft: [-0.1, 0], ArrowRight: [0.1, 0], ArrowUp: [0, -0.1], ArrowDown: [0, 0.1] };
              if (delta[event.key]) { event.preventDefault(); const [dx, dy] = delta[event.key]; onMove(rack.id, Math.max(0, Math.round((x + dx) * 10) / 10), Math.max(0, Math.round((y + dy) * 10) / 10)); }
            }}
            onPointerDown={event => {
              if (!onMove || disabled || event.button !== 0) return;
              event.preventDefault(); event.currentTarget.focus(); event.currentTarget.setPointerCapture(event.pointerId);
              const p = point(event); setDrag({ id: rack.id, startX: p.x - rack.pos_x * CELL_SIZE, startY: p.y - rack.pos_y * CELL_SIZE, x, y });
            }}
            onPointerMove={event => {
              if (!drag || drag.id !== rack.id) return;
              const p = point(event);
              setDrag({ ...drag, x: Math.round(Math.max(0, Math.min((width - RACK_WIDTH - 16) / CELL_SIZE, (p.x - drag.startX) / CELL_SIZE)) * 10) / 10,
                y: Math.round(Math.max(0, Math.min((height - RACK_DEPTH - 16) / CELL_SIZE, (p.y - drag.startY) / CELL_SIZE)) * 10) / 10 });
            }}
            onPointerUp={() => { if (drag && onMove) onMove(rack.id, drag.x, drag.y); setDrag(null); }}
            onPointerCancel={() => setDrag(null)}
            onMouseEnter={() => setHoveredId(rack.id)}
            onMouseLeave={() => setHoveredId(null)}
            style={{ cursor: onMove ? (drag?.id === rack.id ? "grabbing" : "grab") : "pointer", userSelect: "none" }}
          >
            <rect
              width={RACK_WIDTH}
              height={RACK_DEPTH}
              rx={radius.sm}
              fill={isHovered ? colors.surface2 : colors.surface1}
              stroke={isHovered ? colors.accent : colors.border}
              strokeWidth={1.5}
            />
            <text x={RACK_WIDTH / 2} y={RACK_DEPTH / 2 - 4} textAnchor="middle" fill={colors.textPrimary} fontSize={fontSize.md} fontWeight={600}>
              {rack.name}
            </text>
            <text x={RACK_WIDTH / 2} y={RACK_DEPTH / 2 + 12} textAnchor="middle" fill={colors.textMuted} fontSize={fontSize.xs}>
              {rack.u_height}U
            </text>
          </g>
        );
      })}
    </svg>
  );
}
