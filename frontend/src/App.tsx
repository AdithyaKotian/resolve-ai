import { Route, Routes } from "react-router";

import { AdminDashboardPage } from "./pages/AdminDashboardPage";
import { CustomerSupportPage } from "./pages/CustomerSupportPage";
import { NotFoundPage } from "./pages/NotFoundPage";

export default function App() {
  return (
    <Routes>
      <Route
        path="/"
        element={<CustomerSupportPage />}
      />

      <Route
        path="/admin"
        element={<AdminDashboardPage />}
      />

      <Route
        path="*"
        element={<NotFoundPage />}
      />
    </Routes>
  );
}