import { Link } from "react-router-dom";

import { useDataCenters } from "../api/hooks";

export default function DataCenterListPage() {
  const { data: datacenters, isLoading } = useDataCenters();

  if (isLoading) return <div style={{ padding: 24 }}>Loading...</div>;

  return (
    <div style={{ padding: 24 }}>
      <h1>Data Centers</h1>
      <ul>
        {datacenters?.map((dc) => (
          <li key={dc.id}>
            <Link to={`/dc/${dc.id}`}>{dc.name}</Link>
            {dc.location && <span style={{ color: "#9aa5b1" }}> — {dc.location}</span>}
          </li>
        ))}
      </ul>
    </div>
  );
}
