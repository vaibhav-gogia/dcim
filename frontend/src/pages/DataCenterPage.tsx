import { Link, useParams } from "react-router-dom";

import { useDataCenterFloor } from "../api/hooks";
import DataCenterFloorView from "../components/DataCenterFloorView";

export default function DataCenterPage() {
  const { datacenterId } = useParams<{ datacenterId: string }>();
  const { data: floor, isLoading } = useDataCenterFloor(datacenterId!);

  if (isLoading || !floor) return <div style={{ padding: 24 }}>Loading...</div>;

  return (
    <div style={{ padding: 24 }}>
      <Link to="/">← Data Centers</Link>
      <h1>{floor.name}</h1>
      <p style={{ color: "#9aa5b1" }}>Click a rack to view it.</p>
      <DataCenterFloorView racks={floor.racks} />
    </div>
  );
}
