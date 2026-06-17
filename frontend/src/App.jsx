import { Routes, Route, Navigate } from "react-router-dom";
import { useSelector, useDispatch } from "react-redux";
import { useEffect } from "react";
import { fetchProfile } from "./store/slices/authSlice";

import Navbar from "./components/Navbar";
import LandingPage from "./pages/LandingPage";
import LoginPage from "./pages/LoginPage";
import RegisterPage from "./pages/RegisterPage";
import SearchPage from "./pages/SearchPage";
import BookingPage from "./pages/BookingPage";
import MyBookingsPage from "./pages/MyBookingsPage";
import OwnerDashboard from "./pages/OwnerDashboard";
import AdminPanel from "./pages/AdminPanel";
import NotFoundPage from "./pages/NotFoundPage";

// ── Protected Route ───────────────────────────────────────────────────────────
const ProtectedRoute = ({ children, roles }) => {
  const { isAuthenticated, user } = useSelector((s) => s.auth);
  if (!isAuthenticated) return <Navigate to="/login" replace />;
  if (roles && user && !roles.includes(user.role)) return <Navigate to="/" replace />;
  return children;
};

export default function App() {
  const dispatch = useDispatch();
  const { isAuthenticated } = useSelector((s) => s.auth);

  useEffect(() => {
    if (isAuthenticated) dispatch(fetchProfile());
  }, [isAuthenticated]);

  return (
    <div className="min-h-screen">
      <Navbar />
      <Routes>
        <Route path="/"       element={<LandingPage />} />
        <Route path="/login"  element={<LoginPage />} />
        <Route path="/register" element={<RegisterPage />} />

        <Route path="/search" element={
          <ProtectedRoute><SearchPage /></ProtectedRoute>
        } />
        <Route path="/book/:slotId" element={
          <ProtectedRoute><BookingPage /></ProtectedRoute>
        } />
        <Route path="/bookings" element={
          <ProtectedRoute><MyBookingsPage /></ProtectedRoute>
        } />
        <Route path="/owner/*" element={
          <ProtectedRoute roles={["owner"]}><OwnerDashboard /></ProtectedRoute>
        } />
        <Route path="/admin/*" element={
          <ProtectedRoute roles={["admin"]}><AdminPanel /></ProtectedRoute>
        } />
        <Route path="*" element={<NotFoundPage />} />
      </Routes>
    </div>
  );
}
