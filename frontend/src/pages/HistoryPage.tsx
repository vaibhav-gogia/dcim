import PageShell from "../components/PageShell";
import ActionHistory from "../components/ActionHistory";
export default function HistoryPage() {
  return <PageShell crumbs={[{ label: "Data Centers", to: "/" }, { label: "Activity" }]} title="Activity">
    <p>Recorded inventory and power requests. Pending means completion has not yet been observed; unknown outcomes must be checked before retrying.</p>
    <ActionHistory />
  </PageShell>;
}
