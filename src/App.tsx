import { BrowserRouter, Navigate, Route, Routes } from "react-router-dom";
import Dashboard from "./pages/dashboard/Dashboard";
import Customers from "./pages/dashboard/customers/Customers";
import Subscriptions from "./pages/dashboard/subscriptions/Subscriptions";
import Invoices from "./pages/dashboard/invoices/Invoices";
import Payments from "./pages/payments/Payments";
import RevenueInsights from "./pages/ai/RevenueInsights";

function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<Navigate to="/dashboard" replace />} />
        <Route path="/dashboard" element={<Dashboard />} />
        <Route path="/customers" element={<Customers />} />
        <Route path="/subscriptions" element={<Subscriptions />} />
        <Route path="/invoices" element={<Invoices />} />
        <Route path="/payments" element={<Payments />} />
        <Route path="/ai/revenue-insights" element={<RevenueInsights />} />
      </Routes>
    </BrowserRouter>
  );
}

export default App;