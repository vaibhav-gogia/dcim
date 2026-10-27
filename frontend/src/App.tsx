import { useAuth } from "./AuthContext";
import HistoryPage from "./pages/HistoryPage";
import AccountPage from "./pages/AccountPage";
import LoginPage from "./pages/LoginPage";
import { Route, Routes } from "react-router-dom";

import DataCenterListPage from "./pages/DataCenterListPage";
import DataCenterPage from "./pages/DataCenterPage";
import DataHallPage from "./pages/DataHallPage";
import InventoryPage from "./pages/InventoryPage";
import RackPage from "./pages/RackPage";

export default function App() {
  const auth = useAuth();
  if (auth.loading) return <p role="status" style={{ padding: 30 }}>Checking session…</p>;
  if (auth.error) return <div role="alert" style={{ padding: 30 }}>{auth.error} <button onClick={() => auth.reload()}>Retry</button></div>;
  if (!auth.user) return <LoginPage />;
  return (
    <Routes>
      <Route path="/history" element={<HistoryPage />} />
      <Route path="/account" element={<AccountPage />} />
      <Route path="/inventory" element={<InventoryPage />} />
      <Route path="/" element={<DataCenterListPage />} />
      <Route path="/dc/:datacenterId" element={<DataCenterPage />} />
      <Route path="/hall/:dataHallId" element={<DataHallPage />} />
      <Route path="/rack/:rackId" element={<RackPage />} />
    </Routes>
  );
}
