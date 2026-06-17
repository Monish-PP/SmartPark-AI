import { useState } from "react";
import { motion } from "framer-motion";
import { Link, useNavigate } from "react-router-dom";
import { useDispatch, useSelector } from "react-redux";
import { registerUser } from "../store/slices/authSlice";
import {
  RiParkingBoxLine, RiMailLine, RiLockPasswordLine,
  RiUserLine, RiLoader4Line, RiCarLine, RiStoreLine,
} from "react-icons/ri";

export default function RegisterPage() {
  const dispatch = useDispatch();
  const navigate = useNavigate();
  const { loading } = useSelector((s) => s.auth);
  const [form, setForm] = useState({ full_name: "", email: "", password: "", role: "user" });

  const handleSubmit = async (e) => {
    e.preventDefault();
    const result = await dispatch(registerUser(form));
    if (result.meta.requestStatus === "fulfilled") {
      navigate(form.role === "owner" ? "/owner" : "/search");
    }
  };

  return (
    <div className="min-h-[90vh] flex items-center justify-center px-4 py-10">
      <div className="absolute inset-0 overflow-hidden pointer-events-none">
        <div className="absolute top-1/3 left-1/2 -translate-x-1/2 w-[500px] h-[500px]
                        rounded-full bg-accent-600/8 blur-[100px]" />
      </div>

      <motion.div initial={{ opacity: 0, y: 24 }} animate={{ opacity: 1, y: 0 }}
        className="relative z-10 w-full max-w-md">

        <div className="text-center mb-8">
          <div className="inline-flex w-16 h-16 rounded-2xl bg-gradient-to-br from-primary-500 to-accent-600
                          items-center justify-center shadow-glow-md mx-auto mb-4">
            <RiParkingBoxLine className="text-white text-3xl" />
          </div>
          <h1 className="font-display font-bold text-2xl text-white">Join SmartPark AI</h1>
          <p className="text-slate-400 text-sm mt-1">Create your free account</p>
        </div>

        <form onSubmit={handleSubmit} className="glass-card p-8 space-y-5">

          {/* Role selector */}
          <div className="space-y-1.5">
            <label className="text-xs font-medium text-slate-400">I am a</label>
            <div className="grid grid-cols-2 gap-3">
              {[
                { value: "user",  label: "Driver",       icon: <RiCarLine /> },
                { value: "owner", label: "Parking Owner", icon: <RiStoreLine /> },
              ].map((r) => (
                <button key={r.value} type="button"
                  onClick={() => setForm((f) => ({ ...f, role: r.value }))}
                  className={`flex items-center justify-center gap-2 py-3 rounded-xl border text-sm font-medium transition-all
                    ${form.role === r.value
                      ? "border-primary-500/60 bg-primary-500/15 text-primary-300"
                      : "border-white/10 bg-white/5 text-slate-400 hover:border-white/20"
                    }`}>
                  {r.icon} {r.label}
                </button>
              ))}
            </div>
          </div>

          <div className="space-y-1.5">
            <label className="text-xs font-medium text-slate-400">Full Name</label>
            <div className="relative">
              <RiUserLine className="absolute left-3 top-1/2 -translate-y-1/2 text-slate-500" />
              <input type="text" required placeholder="Your full name"
                className="input-field pl-9"
                value={form.full_name}
                onChange={(e) => setForm((f) => ({ ...f, full_name: e.target.value }))} />
            </div>
          </div>

          <div className="space-y-1.5">
            <label className="text-xs font-medium text-slate-400">Email Address</label>
            <div className="relative">
              <RiMailLine className="absolute left-3 top-1/2 -translate-y-1/2 text-slate-500" />
              <input type="email" required placeholder="you@example.com"
                className="input-field pl-9"
                value={form.email}
                onChange={(e) => setForm((f) => ({ ...f, email: e.target.value }))} />
            </div>
          </div>

          <div className="space-y-1.5">
            <label className="text-xs font-medium text-slate-400">Password</label>
            <div className="relative">
              <RiLockPasswordLine className="absolute left-3 top-1/2 -translate-y-1/2 text-slate-500" />
              <input type="password" required placeholder="Min 8 characters"
                className="input-field pl-9" minLength={8}
                value={form.password}
                onChange={(e) => setForm((f) => ({ ...f, password: e.target.value }))} />
            </div>
          </div>

          <button type="submit" disabled={loading} className="btn-primary w-full justify-center py-3.5 text-base">
            {loading ? <><RiLoader4Line className="animate-spin" /> Creating Account...</> : "Create Account →"}
          </button>
        </form>

        <p className="text-center text-slate-400 text-sm mt-6">
          Already have an account?{" "}
          <Link to="/login" className="text-primary-400 hover:text-primary-300 font-medium">Sign in</Link>
        </p>
      </motion.div>
    </div>
  );
}
