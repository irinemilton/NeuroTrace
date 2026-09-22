import { Routes, Route, Navigate } from "react-router-dom";

import BrainAnalysis from "./pages/BrainAnalysis";
import { Dashboard } from "./pages/Dashboard";

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

      <Route
        path="*"
        element={<Navigate to="/" replace />}
      />
    </Routes>
  );
}

export default App;