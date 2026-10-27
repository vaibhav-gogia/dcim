import { useState } from "react";
import { useMutation, useQuery } from "@tanstack/react-query";
import { api } from "../api/client";
import { useAuth, User } from "../AuthContext";
import PageShell from "../components/PageShell";
import { InventoryButton } from "../components/InventoryEditor";
import { colors, radius, space } from "../theme";

const inputStyle = { padding: space.sm, color: colors.textPrimary, background: colors.surface0, border: `1px solid ${colors.border}`, borderRadius: radius.sm, fontSize: 16 };
function UserEditor({ existing, onSave }: { existing?: User; onSave: () => void }) {
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [role, setRole] = useState(existing?.role ?? "viewer");
  const [active, setActive] = useState(existing?.is_active ?? true);
  const save = useMutation({ mutationFn: () => existing ? api.patch(`/users/${existing.id}`, { role, is_active: active, ...(password ? { password } : {}) }) : api.post("/users", { username, password, role }),
    onSuccess: () => { setUsername(""); setPassword(""); onSave(); } });
  return <form aria-label={existing ? `Edit ${existing.username}` : "Create user"} onSubmit={e => { e.preventDefault(); if (existing && !window.confirm(`Update access for ${existing.username}? Their current sessions will be revoked.`)) return; save.mutate(); }} style={{ marginBottom: space.lg, padding: space.md, background: colors.surface1, border: `1px solid ${colors.border}`, borderRadius: radius.sm }}>
    <h3>{existing?.username ?? "Create user"}</h3>
    <fieldset disabled={save.isPending} style={{ display: "flex", gap: space.sm, flexWrap: "wrap", border: 0, padding: 0 }}>
      {!existing && <label>Username<input style={inputStyle} required minLength={3} maxLength={64} pattern="[a-z0-9][a-z0-9_.-]*" value={username} onChange={e => setUsername(e.target.value)} /></label>}
      <label>{existing ? "Reset password (optional)" : "Initial password"}<input style={inputStyle} type="password" autoComplete="new-password" required={!existing} minLength={12} maxLength={128} value={password} onChange={e => setPassword(e.target.value)} /></label>
      <label>Role<select style={inputStyle} value={role} onChange={e => setRole(e.target.value as User['role'])}>{["viewer", "operator", "admin"].map(r => <option key={r}>{r}</option>)}</select></label>
      {existing && <label><input type="checkbox" checked={active} onChange={e => setActive(e.target.checked)} />Active</label>}
      <InventoryButton type="submit">{save.isPending ? "Saving…" : existing ? "Save user" : "Create user"}</InventoryButton>
    </fieldset>
    {save.error && <p role="alert" style={{ color: colors.statusCritical }}>{save.error.message}</p>}
    {save.isSuccess && <p role="status">Saved.</p>}
  </form>;
}
export default function AccountPage() {
  const auth = useAuth();
  const users = useQuery({ queryKey: ["users"], queryFn: () => api.get<User[]>("/users"), enabled: auth.user?.role === "admin" });
  const [currentPassword, setCurrentPassword] = useState("");
  const [newPassword, setNewPassword] = useState("");
  const change = useMutation({ mutationFn: () => api.post("/auth/password", { current_password: currentPassword, new_password: newPassword }), onSuccess: () => { setCurrentPassword(""); setNewPassword(""); void auth.reload(); } });
  return <PageShell crumbs={[{ label: "Data Centers", to: "/" }, { label: "Account" }]} title="Account">
    <p>Signed in as <strong>{auth.user?.username}</strong> · {auth.user?.role}</p>
    <h2>Change your password</h2><p>Changing your password signs out all your sessions.</p>
    <form onSubmit={e => { e.preventDefault(); change.mutate(); }} style={{ display: "grid", gap: space.sm, maxWidth: 420 }}>
      <label>Current password<input style={inputStyle} type="password" autoComplete="current-password" required maxLength={128} value={currentPassword} onChange={e => setCurrentPassword(e.target.value)} /></label>
      <label>New password<input style={inputStyle} type="password" autoComplete="new-password" required minLength={12} maxLength={128} value={newPassword} onChange={e => setNewPassword(e.target.value)} /></label>
      <InventoryButton disabled={change.isPending} type="submit">Change password</InventoryButton>
      {change.error && <p role="alert">{change.error.message}</p>}
    </form>
    {auth.user?.role === "admin" && <section style={{ marginTop: space.xl }}><h2>Manage users</h2><p>Viewers browse. Operators also control power. Administrators manage inventory and accounts. Passwords require 12–128 characters.</p>
      <UserEditor onSave={() => users.refetch()} />
      {users.error && <p role="alert">{users.error.message}</p>}
      {users.data?.map(user => <UserEditor key={`${user.id}-${user.role}-${user.is_active}`} existing={user} onSave={() => { if (user.id === auth.user?.id) void auth.reload(); else void users.refetch(); }} />)}
    </section>}
  </PageShell>;
}
