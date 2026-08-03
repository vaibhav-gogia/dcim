export function TempGauge({ label, value }: { label: string; value: number }) {
  const pct = Math.min(100, Math.max(0, ((value - 15) / (70 - 15)) * 100));
  const color = value > 60 ? "#c0392b" : value > 45 ? "#d4a017" : "#2e8b57";
  return (
    <div style={{ marginBottom: 6 }}>
      <div style={{ display: "flex", justifyContent: "space-between", fontSize: 12 }}>
        <span>{label}</span>
        <span>{value.toFixed(1)}°C</span>
      </div>
      <div style={{ background: "#2a3340", borderRadius: 4, height: 6 }}>
        <div style={{ width: `${pct}%`, background: color, height: "100%", borderRadius: 4 }} />
      </div>
    </div>
  );
}

export function FanGauge({ label, rpm }: { label: string; rpm: number }) {
  return (
    <div style={{ display: "flex", justifyContent: "space-between", fontSize: 12, marginBottom: 4 }}>
      <span>{label}</span>
      <span>{rpm.toLocaleString()} RPM</span>
    </div>
  );
}

export function PsuStatus({ label, status }: { label: string; status: string }) {
  const ok = status === "ok";
  return (
    <div style={{ display: "flex", justifyContent: "space-between", fontSize: 12, marginBottom: 4 }}>
      <span>{label}</span>
      <span style={{ color: ok ? "#2e8b57" : "#b04040" }}>{status}</span>
    </div>
  );
}
