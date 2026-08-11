import { colors, fontSize, radius, space } from "../theme";

const TEMP_MIN = 15;
const TEMP_MAX = 70;
const TEMP_WARNING = 50;
const TEMP_CRITICAL = 60;
const FAN_MAX_RPM = 7000;

function Meter({ pct, color }: { pct: number; color: string }) {
  const clamped = Math.min(100, Math.max(0, pct));
  return (
    <div style={{ background: colors.accentTrack, borderRadius: radius.sm, height: 6 }}>
      <div style={{ width: `${clamped}%`, background: color, height: "100%", borderRadius: radius.sm }} />
    </div>
  );
}

function MeterRow({ label, valueText, pct, color }: { label: string; valueText: string; pct: number; color: string }) {
  return (
    <div style={{ marginBottom: space.sm }}>
      <div style={{ display: "flex", justifyContent: "space-between", fontSize: fontSize.sm, color: colors.textSecondary, marginBottom: 3 }}>
        <span>{label}</span>
        <span style={{ fontVariantNumeric: "tabular-nums", color: colors.textPrimary }}>{valueText}</span>
      </div>
      <Meter pct={pct} color={color} />
    </div>
  );
}

export function TempGauge({ label, value }: { label: string; value: number }) {
  const color = value >= TEMP_CRITICAL ? colors.statusCritical : value >= TEMP_WARNING ? colors.statusWarning : colors.accent;
  const pct = ((value - TEMP_MIN) / (TEMP_MAX - TEMP_MIN)) * 100;
  return <MeterRow label={label} valueText={`${value.toFixed(1)}°C`} pct={pct} color={color} />;
}

export function FanGauge({ label, rpm }: { label: string; rpm: number }) {
  const pct = (rpm / FAN_MAX_RPM) * 100;
  return <MeterRow label={label} valueText={`${rpm.toLocaleString()} RPM`} pct={pct} color={colors.accent} />;
}

export function PsuStatus({ label, status }: { label: string; status: string }) {
  const ok = status === "ok";
  const color = ok ? colors.successText : colors.statusCritical;
  const glyph = ok ? "●" : "!";
  return (
    <div style={{ display: "flex", justifyContent: "space-between", fontSize: fontSize.sm, marginBottom: space.xs, color: colors.textSecondary }}>
      <span>{label}</span>
      <span style={{ color }}>
        {glyph} {status}
      </span>
    </div>
  );
}
