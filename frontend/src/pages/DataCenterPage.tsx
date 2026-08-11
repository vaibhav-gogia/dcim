import { useParams } from "react-router-dom";

import { useDataCenterFloor } from "../api/hooks";
import DataCenterFloorView from "../components/DataCenterFloorView";
import PageShell from "../components/PageShell";
import { colors } from "../theme";

export default function DataCenterPage() {
  const { datacenterId } = useParams<{ datacenterId: string }>();
  const { data: floor, isLoading } = useDataCenterFloor(datacenterId!);

  if (isLoading || !floor) {
    return (
      <PageShell crumbs={[{ label: "Data Centers", to: "/" }]} title="Loading...">
        <div style={{ color: colors.textMuted }}>Loading...</div>
      </PageShell>
    );
  }

  return (
    <PageShell crumbs={[{ label: "Data Centers", to: "/" }, { label: floor.name }]} title={floor.name}>
      <p style={{ color: colors.textMuted, marginTop: 0 }}>Click a rack to view it.</p>
      <DataCenterFloorView racks={floor.racks} />
    </PageShell>
  );
}
