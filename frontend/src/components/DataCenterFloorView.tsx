import { useNavigate } from "react-router-dom";

import { FloorRack } from "../api/types";

const CELL_SIZE = 130;
const RACK_WIDTH = 90;
const RACK_DEPTH = 70;

export default function DataCenterFloorView({ racks }: { racks: FloorRack[] }) {
  const navigate = useNavigate();

  const maxX = Math.max(1, ...racks.map((r) => r.pos_x));
  const maxY = Math.max(1, ...racks.map((r) => r.pos_y));

  return (
    <svg
      width="100%"
      viewBox={`0 0 ${(maxX + 1) * CELL_SIZE} ${(maxY + 1) * CELL_SIZE}`}
      style={{ background: "var(--floor-bg, #12161c)", borderRadius: 8 }}
    >
      {racks.map((rack) => (
        <g
          key={rack.id}
          transform={`translate(${rack.pos_x * CELL_SIZE + 20}, ${rack.pos_y * CELL_SIZE + 20})`}
          onClick={() => navigate(`/rack/${rack.id}`)}
          style={{ cursor: "pointer" }}
        >
          <rect
            width={RACK_WIDTH}
            height={RACK_DEPTH}
            rx={6}
            fill="#2a3340"
            stroke="#4a5568"
            strokeWidth={1.5}
          />
          <text x={RACK_WIDTH / 2} y={RACK_DEPTH / 2 - 4} textAnchor="middle" fill="#e2e8f0" fontSize={13}>
            {rack.name}
          </text>
          <text x={RACK_WIDTH / 2} y={RACK_DEPTH / 2 + 14} textAnchor="middle" fill="#9aa5b1" fontSize={11}>
            {rack.u_height}U
          </text>
        </g>
      ))}
    </svg>
  );
}
