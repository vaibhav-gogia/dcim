import { Fragment, useEffect, useRef, useState } from "react";
import { useMutation, useQuery } from "@tanstack/react-query";
import { api } from "../api/client";
import { useAuth, User } from "../AuthContext";
import PageShell from "../components/PageShell";
import { InventoryButton } from "../components/InventoryEditor";
import { colors } from "../theme";

function UserEditor({ existing, onSave, onCancel }: { existing?: User; onSave: () => void; onCancel: () => void }) {
  const heading = useRef<HTMLHeadingElement>(null);
  useEffect(() => { heading.current?.scrollIntoView({ block: "nearest" }); heading.current?.focus({ preventScroll: true }); }, []);
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [role, setRole] = useState(existing?.role ?? "viewer");
  const [active, setActive] = useState(existing?.is_active ?? true);
  const save = useMutation({ mutationFn: () => existing ? api.patch(`/users/${existing.id}`, { role, is_active: active, ...(password ? { password } : {}) }) : api.post("/users", { username, password, role }),
    onSuccess: () => { setUsername(""); setPassword(""); onSave(); } });
  return <form aria-label={existing ? `Edit ${existing.username}` : "Create user"} onSubmit={e => { e.preventDefault(); if (existing && !window.confirm(`Update access for ${existing.username}? Their current sessions will be revoked.`)) return; save.mutate(); }} className="account-card">
    <h3 ref={heading} tabIndex={-1} className="account-card-title">{existing ? `Edit user: ${existing.username}` : "Create user"}</h3>
    <fieldset disabled={save.isPending} className="account-fields">
      {!existing && <label className="account-field">Username<input className="account-input" required minLength={3} maxLength={64} pattern="[a-z0-9][a-z0-9_.-]*" value={username} onChange={e => setUsername(e.target.value)} /></label>}
      <label className="account-field">{existing ? "Reset password (optional)" : "Initial password"}<input className="account-input" type="password" autoComplete="new-password" required={!existing} minLength={12} maxLength={128} value={password} onChange={e => setPassword(e.target.value)} /></label>
      <label className="account-field">Role<select className="account-input" value={role} onChange={e => setRole(e.target.value as User['role'])}>{["viewer", "operator", "admin"].map(r => <option key={r}>{r}</option>)}</select></label>
      {existing && <div className="account-field"><span>Account status</span><label className="account-checkbox"><input type="checkbox" checked={active} onChange={e => setActive(e.target.checked)} />Active</label></div>}
      <div className="account-form-actions"><InventoryButton type="submit">{save.isPending ? "Saving…" : existing ? "Save user" : "Create user"}</InventoryButton><InventoryButton type="button" onClick={onCancel}>Cancel</InventoryButton></div>
    </fieldset>
    {save.error && <p className="account-feedback" role="alert" style={{ color: colors.statusCritical }}>{save.error.message}</p>}
    {save.isSuccess && <p className="account-feedback" role="status">Saved.</p>}
  </form>;
}
function UserManagement() {
  const auth = useAuth();
  const users = useQuery({ queryKey: ["users"], queryFn: () => api.get<User[]>("/users") });
  const [query, setQuery] = useState("");
  const [role, setRole] = useState("");
  const [status, setStatus] = useState("");
  const [editor, setEditor] = useState<User | "new" | null>(null);
  const [notice, setNotice] = useState("");
  const matches = users.data?.filter(user => user.username.toLowerCase().includes(query.trim().toLowerCase()) && (!role || user.role === role) && (!status || user.is_active === (status === "active"))) ?? [];
  async function saved() {
    const editedSelf = editor !== "new" && editor?.id === auth.user?.id;
    setNotice(editor === "new" ? "User created." : "User updated. Their previous sessions have been revoked.");
    setEditor(null);
    await users.refetch();
    if (editedSelf) await auth.reload();
  }
  return <section className="account-section" aria-labelledby="users-heading">
    <div className="account-users-heading"><h2 id="users-heading" className="account-section-title">Users</h2><InventoryButton onClick={() => { setNotice(""); setEditor("new"); }}>Add user</InventoryButton></div>
    <p className="account-description">Manage access for your team. Disable accounts to block sign-in while keeping their action history.</p>
    {notice && <p role="status">{notice}</p>}
    {editor === "new" && <UserEditor key="new" onSave={() => void saved()} onCancel={() => setEditor(null)} />}
    <div className="account-users-filters">
      <label className="account-field">Search users<input className="account-input" type="search" placeholder="Username" value={query} onChange={e => setQuery(e.target.value)} /></label>
      <label className="account-field">Role<select className="account-input" value={role} onChange={e => setRole(e.target.value)}><option value="">All roles</option>{["viewer", "operator", "admin"].map(value => <option key={value}>{value}</option>)}</select></label>
      <label className="account-field">Status<select className="account-input" value={status} onChange={e => setStatus(e.target.value)}><option value="">All statuses</option><option value="active">Active</option><option value="disabled">Disabled</option></select></label>
    </div>
    {users.isPending ? <p role="status">Loading users…</p> : users.error ? <p role="alert">{users.error.message} <InventoryButton onClick={() => users.refetch()}>Retry</InventoryButton></p> : <>
      <p style={{ color: colors.textSecondary }}>{matches.length} of {users.data?.length ?? 0} users</p>
      <div className="account-users-table"><table>
        <caption className="account-table-caption">Team accounts</caption>
        <thead><tr><th scope="col">Username</th><th scope="col">Role</th><th scope="col">Status</th><th scope="col">Actions</th></tr></thead>
        <tbody>{matches.map(user => <Fragment key={user.id}><tr>
          <td><strong>{user.username}</strong>{user.id === auth.user?.id && <span style={{ color: colors.textMuted }}> (you)</span>}</td>
          <td style={{ textTransform: "capitalize" }}>{user.role}</td>
          <td><span className={`account-user-status${user.is_active ? " is-active" : ""}`}>{user.is_active ? "Active" : "Disabled"}</span></td>
          <td><InventoryButton type="button" aria-label={`Edit ${user.username}`} aria-expanded={editor !== "new" && editor?.id === user.id} aria-controls={`user-editor-${user.id}`} onClick={() => { setNotice(""); setEditor(user); }}>Edit</InventoryButton></td>
        </tr>
        {editor !== "new" && editor?.id === user.id && <tr id={`user-editor-${user.id}`} className="account-user-editor-row"><td colSpan={4}>
          <UserEditor key={user.id} existing={user} onSave={() => void saved()} onCancel={() => setEditor(null)} />
        </td></tr>}
        </Fragment>)}
        {!matches.length && <tr><td colSpan={4}>No users match these filters.</td></tr>}</tbody>
      </table></div>
    </>}
    <p className="account-description" style={{ marginTop: 15 }}>Edit a user to change their role, disable/reactivate access, or reset their password. Passwords require 12–128 characters.</p>
  </section>;
}

export default function AccountPage() {
  const auth = useAuth();
  const [currentPassword, setCurrentPassword] = useState("");
  const [newPassword, setNewPassword] = useState("");
  const change = useMutation({ mutationFn: () => api.post("/auth/password", { current_password: currentPassword, new_password: newPassword }), onSuccess: () => { setCurrentPassword(""); setNewPassword(""); void auth.reload(); } });
  return <PageShell crumbs={[{ label: "Data Centers", to: "/" }, { label: "Account" }]} title="Account">
    <div className="account-page">
    <p className="account-description">Signed in as <strong>{auth.user?.username}</strong> · {auth.user?.role}</p>
    <section className="account-card" aria-labelledby="password-heading">
      <h2 id="password-heading" className="account-card-title">Change your password</h2>
      <p className="account-description">Changing your password signs out all your sessions.</p>
      <form onSubmit={e => { e.preventDefault(); change.mutate(); }}>
        <fieldset className="account-fields" disabled={change.isPending}>
          <label className="account-field">Current password<input className="account-input" type="password" autoComplete="current-password" required maxLength={128} value={currentPassword} onChange={e => setCurrentPassword(e.target.value)} /></label>
          <label className="account-field">New password<input className="account-input" type="password" autoComplete="new-password" required minLength={12} maxLength={128} value={newPassword} onChange={e => setNewPassword(e.target.value)} /></label>
          <div className="account-form-actions"><InventoryButton type="submit">{change.isPending ? "Changing…" : "Change password"}</InventoryButton></div>
        </fieldset>
        {change.error && <p className="account-feedback" role="alert" style={{ color: colors.statusCritical }}>{change.error.message}</p>}
      </form>
    </section>
    {auth.user?.role === "admin" && <UserManagement />}
    </div>
  </PageShell>;
}
