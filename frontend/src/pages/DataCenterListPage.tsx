import { useNavigate } from "react-router-dom";

import { useDataCenters } from "../api/hooks";
import PageShell from "../components/PageShell";
import { colors, fontSize, radius, space } from "../theme";

export default function DataCenterListPage() {
  const navigate = useNavigate();
  const { data: datacenters, isLoading } = useDataCenters();

  return (
    <PageShell crumbs={[{ label: "DCIM" }]} title="Data Centers">
      {isLoading ? (
        <div style={{ color: colors.textMuted }}>Loading...</div>
      ) : !datacenters?.length ? (
        <div style={{ color: colors.textMuted }}>No data centers yet.</div>
      ) : (
        <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fill, minmax(275px, 1fr))", gap: space.lg, maxWidth: 1100 }}>
          {datacenters.map((dc) => (
            <div
              key={dc.id}
              onClick={() => navigate(`/dc/${dc.id}`)}
              style={{
                padding: space.lg,
                background: colors.surface1,
                border: `1px solid ${colors.border}`,
                borderRadius: radius.md,
                cursor: "pointer",
              }}
            >
              <div style={{ fontSize: fontSize.lg, fontWeight: 600, color: colors.textPrimary, marginBottom: space.xs }}>{dc.name}</div>
              {dc.location && <div style={{ fontSize: fontSize.sm, color: colors.textMuted }}>{dc.location}</div>}
            </div>
          ))}
        </div>
      )}
    </PageShell>
  );
}
