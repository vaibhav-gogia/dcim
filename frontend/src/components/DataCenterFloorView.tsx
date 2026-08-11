import { useState } from "react";
import { useNavigate } from "react-router-dom";

import { FloorRack } from "../api/types";
import { colors, fontSize, radius } from "../theme";

const CELL_SIZE = 200; //grid spacing between racks
const RACK_WIDTH = 150; //rack tile width
const RACK_DEPTH = 110; //rack tile depth
const DOT_SPACING = 4; //floor dot-grid spacing

export default function DataCenterFloorView({ racks }: { racks: FloorRack[] }) {
  const navigate = useNavigate();
  const [hoveredId, setHoveredId] = useState<string | null>(null);

  const maxX = Math.max(1, ...racks.map((r) => r.pos_x));
  const maxY = Math.max(1, ...racks.map((r) => r.pos_y));
  const width = (maxX + 1) * CELL_SIZE;
  const height = (maxY + 1) * CELL_SIZE;

  return (
    <svg
      width="100%"
      viewBox={`0 0 ${width} ${height}`}
      style={{ maxWidth: width, borderRadius: radius.md, border: `1px solid ${colors.border}` }}
    >
      <defs>
        <pattern id="floor-dots" width={DOT_SPACING} height={DOT_SPACING} patternUnits="userSpaceOnUse">
          <circle cx={1} cy={1} r={1} fill={colors.gridline} />
        </pattern>
      </defs>
      <rect width={width} height={height} fill={colors.surface0} />
      <rect width={width} height={height} fill="url(#floor-dots)" />

      {racks.map((rack) => {
        const isHovered = rack.id === hoveredId;
        return (
          <g
            key={rack.id}
            transform={`translate(${rack.pos_x * CELL_SIZE + 16}, ${rack.pos_y * CELL_SIZE + 16})`}
            onClick={() => navigate(`/rack/${rack.id}`)}
            onMouseEnter={() => setHoveredId(rack.id)}
            onMouseLeave={() => setHoveredId(null)}
            style={{ cursor: "pointer" }}
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
