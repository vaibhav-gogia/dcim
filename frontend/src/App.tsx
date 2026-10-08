import { Route, Routes } from "react-router-dom";

import DataCenterListPage from "./pages/DataCenterListPage";
import DataCenterPage from "./pages/DataCenterPage";
import DataHallPage from "./pages/DataHallPage";
import InventoryPage from "./pages/InventoryPage";
import RackPage from "./pages/RackPage";

export default function App() {
  return (
    <Routes>
      <Route path="/inventory" element={<InventoryPage />} />
      <Route path="/" element={<DataCenterListPage />} />
      <Route path="/dc/:datacenterId" element={<DataCenterPage />} />
      <Route path="/hall/:dataHallId" element={<DataHallPage />} />
      <Route path="/rack/:rackId" element={<RackPage />} />
    </Routes>
  );
}
