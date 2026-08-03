import { Route, Routes } from "react-router-dom";

import DataCenterListPage from "./pages/DataCenterListPage";
import DataCenterPage from "./pages/DataCenterPage";
import RackPage from "./pages/RackPage";

export default function App() {
  return (
    <Routes>
      <Route path="/" element={<DataCenterListPage />} />
      <Route path="/dc/:datacenterId" element={<DataCenterPage />} />
      <Route path="/rack/:rackId" element={<RackPage />} />
    </Routes>
  );
}
