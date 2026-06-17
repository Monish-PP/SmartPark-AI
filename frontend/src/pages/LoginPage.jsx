import { useState } from "react";
import { motion } from "framer-motion";
import { Link, useNavigate } from "react-router-dom";
import { useDispatch, useSelector } from "react-redux";
import { loginUser } from "../store/slices/authSlice";
import { RiParkingBoxLine, RiMailLine, RiLockPasswordLine, RiLoader4Line, RiEyeLine, RiEyeOffLine } from "react-icons/ri";

export default function LoginPage() {
  const dispatch = useDispatch();
  const navigate = useNavigate();
  const { loading } = useSelector((s) => s.auth);
  const [form, setForm] = useState({ email: "", password: "" });
  const [showPass, setShowPass] = useState(false);

  const handleSubmit = async (e) => {
    e.preventDefault();
    const result = await dispatch(loginUser(form));
    if (result.meta.requestStatus === "fulfilled") navigate("/search");
  };

  return (
    <div className="min-h-[90vh] flex items-center justify-center px-4 py-10">
      <div className="absolute inset-0 overflow-hidden pointer-events-none">
        <div className="absolute top-1/3 left-1/2 -translate-x-1/2 w-[500px] h-[500px]
                        rounded-full bg-primary-600/8 blur-[100px]" />
      </div>

      <motion.div initial={{ opacity: 0, y: 24 }} animate={{ opacity: 1, y: 0 }}
        className="relative z-10 w-full max-w-md">

        {/* Logo */}
        <div className="text-center mb-8">
          <div className="inline-flex w-16 h-16 rounded-2xl bg-gradient-to-br from-primary-500 to-accent-600
                          items-center justify-center shadow-glow-md mx-auto mb-4">
            <RiParkingBoxLine className="text-white text-3xl" />
          </div>
          <h1 className="font-display font-bold text-2xl text-white">Welcome back</h1>
          <p className="text-slate-400 text-sm mt-1">Sign in to SmartPark AI</p>
        </div>

        <form onSubmit={handleSubmit} className="glass-card p-8 space-y-5">
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
              <input type={showPass ? "text" : "password"} required placeholder="••••••••"
                className="input-field pl-9 pr-10"
                value={form.password}
                onChange={(e) => setForm((f) => ({ ...f, password: e.target.value }))} />
              <button type="button" onClick={() => setShowPass(!showPass)}
                className="absolute right-3 top-1/2 -translate-y-1/2 text-slate-500 hover:text-white">
                {showPass ? <RiEyeOffLine /> : <RiEyeLine />}
              </button>
            </div>
          </div>

          <button type="submit" disabled={loading} className="btn-primary w-full justify-center py-3.5 text-base">
            {loading ? <><RiLoader4Line className="animate-spin" /> Signing in...</> : "Sign In"}
          </button>
        </form>

        <p className="text-center text-slate-400 text-sm mt-6">
          Don't have an account?{" "}
          <Link to="/register" className="text-primary-400 hover:text-primary-300 font-medium">
            Create one free
          </Link>
        </p>
      </motion.div>
    </div>
  );
}
