import { Link, useNavigate, useLocation } from "react-router-dom";
import { useDispatch, useSelector } from "react-redux";
import { motion, AnimatePresence } from "framer-motion";
import { useState } from "react";
import { logout } from "../store/slices/authSlice";
import {
  RiParkingBoxLine, RiSearchLine, RiDashboard2Line,
  RiLogoutBoxLine, RiMenuLine, RiCloseLine,
  RiUserLine, RiCarLine,
} from "react-icons/ri";

export default function Navbar() {
  const dispatch = useDispatch();
  const navigate = useNavigate();
  const { pathname } = useLocation();
  const { isAuthenticated, user } = useSelector((s) => s.auth);
  const [menuOpen, setMenuOpen] = useState(false);

  const navItems = isAuthenticated
    ? [
        { label: "Search Parking", icon: <RiSearchLine />, to: "/search" },
        { label: "My Bookings",    icon: <RiCarLine />,    to: "/bookings" },
        ...(user?.role === "owner" ? [{ label: "Dashboard", icon: <RiDashboard2Line />, to: "/owner" }] : []),
        ...(user?.role === "admin" ? [{ label: "Admin",     icon: <RiDashboard2Line />, to: "/admin"  }] : []),
      ]
    : [];

  const isActive = (to) => pathname.startsWith(to);

  return (
    <nav className="sticky top-0 z-50 w-full border-b border-white/8 bg-surface-950/80 backdrop-blur-xl">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 h-16 flex items-center justify-between">
        {/* Logo */}
        <Link to="/" className="flex items-center gap-2 group">
          <div className="w-9 h-9 rounded-xl bg-gradient-to-br from-primary-500 to-accent-600
                          flex items-center justify-center shadow-glow-sm
                          group-hover:shadow-glow-md transition-all duration-300">
            <RiParkingBoxLine className="text-white text-xl" />
          </div>
          <span className="font-display font-bold text-lg">
            Smart<span className="text-gradient">Park</span> AI
          </span>
        </Link>

        {/* Desktop Nav */}
        <div className="hidden md:flex items-center gap-1">
          {navItems.map((item) => (
            <Link
              key={item.to}
              to={item.to}
              className={isActive(item.to) ? "nav-link-active" : "nav-link"}
            >
              <span className="flex items-center gap-1.5">
                {item.icon} {item.label}
              </span>
            </Link>
          ))}
        </div>

        {/* Right Actions */}
        <div className="hidden md:flex items-center gap-3">
          {isAuthenticated ? (
            <div className="flex items-center gap-3">
              <div className="flex items-center gap-2 px-3 py-1.5 rounded-lg bg-white/5 border border-white/8">
                <div className="w-6 h-6 rounded-full bg-gradient-to-br from-primary-500 to-accent-500
                                flex items-center justify-center text-xs font-bold text-white">
                  {user?.full_name?.[0] || "U"}
                </div>
                <span className="text-sm text-slate-300">{user?.full_name?.split(" ")[0]}</span>
                <span className="badge-primary text-xs">{user?.role}</span>
              </div>
              <button onClick={() => { dispatch(logout()); navigate("/"); }} className="btn-ghost text-danger">
                <RiLogoutBoxLine /> Logout
              </button>
            </div>
          ) : (
            <div className="flex items-center gap-2">
              <Link to="/login"    className="btn-ghost">Sign In</Link>
              <Link to="/register" className="btn-primary">Get Started</Link>
            </div>
          )}
        </div>

        {/* Mobile Hamburger */}
        <button
          className="md:hidden btn-ghost p-2"
          onClick={() => setMenuOpen(!menuOpen)}
        >
          {menuOpen ? <RiCloseLine size={22} /> : <RiMenuLine size={22} />}
        </button>
      </div>

      {/* Mobile Menu */}
      <AnimatePresence>
        {menuOpen && (
          <motion.div
            initial={{ opacity: 0, height: 0 }}
            animate={{ opacity: 1, height: "auto" }}
            exit={{ opacity: 0, height: 0 }}
            className="md:hidden border-t border-white/8 bg-surface-900/95 backdrop-blur-xl"
          >
            <div className="max-w-7xl mx-auto px-4 py-4 flex flex-col gap-2">
              {navItems.map((item) => (
                <Link
                  key={item.to}
                  to={item.to}
                  className={`flex items-center gap-2 px-4 py-3 rounded-xl text-sm font-medium
                    ${isActive(item.to)
                      ? "bg-primary-500/15 text-primary-300"
                      : "text-slate-400 hover:text-white hover:bg-white/8"
                    } transition-all`}
                  onClick={() => setMenuOpen(false)}
                >
                  {item.icon} {item.label}
                </Link>
              ))}
              {!isAuthenticated && (
                <>
                  <Link to="/login"    className="btn-ghost justify-center" onClick={() => setMenuOpen(false)}>Sign In</Link>
                  <Link to="/register" className="btn-primary justify-center" onClick={() => setMenuOpen(false)}>Get Started</Link>
                </>
              )}
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </nav>
  );
}
