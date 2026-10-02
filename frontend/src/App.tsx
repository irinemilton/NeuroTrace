import { Routes, Route, Navigate } from "react-router-dom";

import BrainAnalysis from "./pages/BrainAnalysis";
import { Dashboard } from "./pages/Dashboard";

import LiveDemo from "./pages/LiveDemo";
import LiveDemoResult from "./pages/LiveDemoResult";
import PatientDashboard from "./pages/PatientDashboard";
import CaretakerDashboard from "./pages/CaretakerDashboard";
import RolePortal from "./pages/RolePortal";
function App() {
  return (
    <Routes>
      <Route path="/" element={<Dashboard />} />

      <Route
        path="/dashboard"
        element={<Dashboard />}
      />

      <Route
        path="/analyze"
        element={<BrainAnalysis />}
      />

      <Route
        path="/analyze/:subjectId"
        element={<BrainAnalysis />}
      />
      <Route path="/live-demo/result/:subjectId" element={<LiveDemoResult />} />
      <Route path="/patient" element={<PatientDashboard />} />
      <Route path="/caretaker" element={<CaretakerDashboard />} />
      <Route path="/portal" element={<RolePortal />} />

      <Route
        path="*"
        element={<Navigate to="/" replace />}
      />
    
        <Route path="/live-demo" element={<LiveDemo />} />
</Routes>
  );
}

export default App;
