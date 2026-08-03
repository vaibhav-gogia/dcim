import { RackElevation as RackElevationData, SystemElevation } from "../api/types";
import { isTransient, POWER_STATE_COLOR } from "./powerColors";

const U_HEIGHT_PX = 18;
const RACK_WIDTH_PX = 240;

export default function RackElevation({
  rack,
  selectedSystemId,
  onSelectSystem,
}: {
  rack: RackElevationData;
  selectedSystemId: string | null;
  onSelectSystem: (system: SystemElevation) => void;
}) {
  const totalHeight = rack.u_height * U_HEIGHT_PX;

  return (
    <svg width={RACK_WIDTH_PX} height={totalHeight + 20} viewBox={`0 0 ${RACK_WIDTH_PX} ${totalHeight + 20}`}>
      <rect x={0} y={10} width={RACK_WIDTH_PX} height={totalHeight} fill="#1a2029" stroke="#4a5568" />
      {rack.systems.map((system) => {
        const yFromTop = rack.u_height - system.u_position - system.u_height + 1;
        const y = 10 + (yFromTop - 1) * U_HEIGHT_PX;
        const height = system.u_height * U_HEIGHT_PX;
        const color = POWER_STATE_COLOR[system.power_state];
        const isSelected = system.id === selectedSystemId;

        return (
          <g key={system.id} onClick={() => onSelectSystem(system)} style={{ cursor: "pointer" }}>
            <rect
              x={4}
              y={y + 1}
              width={RACK_WIDTH_PX - 8}
              height={height - 2}
              rx={3}
              fill={color}
              opacity={isTransient(system.power_state) ? 0.75 : 0.9}
              stroke={isSelected ? "#ffffff" : "#0f1319"}
              strokeWidth={isSelected ? 2 : 1}
            />
            <text x={10} y={y + height / 2 + 4} fontSize={11} fill="#0f1319">
              {system.name}
            </text>
          </g>
        );
      })}
    </svg>
  );
}
