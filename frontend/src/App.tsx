import { useState, type JSX } from "react";
import { BrowserRouter, Routes, Route, Navigate } from "react-router-dom";
import Login from "./pages/Login";
import Register from "./pages/Register";
import Generate from "./pages/Generate";
import Preview from "./pages/Preview";

function App() {
  const [jobId, setJobId] = useState<string | null>(null);
  const token = localStorage.getItem("access_token");

  const PrivateRoute = ({ children }: { children: JSX.Element }) => {
    return token ? children : <Navigate to="/login" />;
  };

  return (
    <BrowserRouter>
      <Routes>
        <Route path="/login" element={<Login />} />
        <Route path="/register" element={<Register />} />

        <Route
          path="/"
          element={
            <PrivateRoute>
              {jobId ? (
                <Preview jobId={jobId} onBack={() => setJobId(null)} />
              ) : (
                <Generate onCreated={setJobId} />
              )}
            </PrivateRoute>
          }
        />
      </Routes>
    </BrowserRouter>
  );
}

export default App;