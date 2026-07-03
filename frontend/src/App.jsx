import React from "react";
import { Routes, Route } from "react-router-dom";
import Navbar from "./components/shared/Navbar";
import ErrorBoundary from "./components/shared/ErrorBoundary";
import HomePage from "./pages/HomePage";
import AdminPage from "./pages/AdminPage";
import EmployeePage from "./pages/EmployeePage";

export default function App() {
  return (
    <div className="app-shell">
      <Navbar />
      <ErrorBoundary>
        <Routes>
          <Route path="/" element={<HomePage />} />
          <Route path="/admin/*" element={<AdminPage />} />
          <Route path="/employee" element={<EmployeePage />} />
          <Route path="*" element={<HomePage />} />
        </Routes>
      </ErrorBoundary>
    </div>
  );
}
