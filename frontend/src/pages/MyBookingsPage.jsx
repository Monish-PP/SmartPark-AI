import { useEffect, useState } from "react";
import { motion } from "framer-motion";
import { bookingAPI } from "../services/api";
import { format } from "date-fns";
import {
  RiParkingBoxLine, RiCheckLine, RiTimeLine, RiLoader4Line,
  RiCloseCircleLine, RiArrowRightLine, RiRefundLine,
} from "react-icons/ri";
import toast from "react-hot-toast";

const STATUS_BADGE = {
  pending:   "badge-warning",
  confirmed: "badge-primary",
  active:    "badge-success",
  completed: "bg-slate-700/50 border-slate-600/50 text-slate-300",
  cancelled: "badge-danger",
  refunded:  "badge-success",
};

const STATUS_ICON = {
  pending:   <RiTimeLine />,
  confirmed: <RiCheckLine />,
  active:    <RiParkingBoxLine />,
  completed: <RiCheckLine />,
  cancelled: <RiCloseCircleLine />,
  refunded:  <RiRefundLine />,
};

export default function MyBookingsPage() {
  const [bookings, setBookings] = useState([]);
  const [loading, setLoading] = useState(true);
  const [actionLoading, setActionLoading] = useState(null);

  const fetchBookings = async () => {
    try {
      const { data } = await bookingAPI.list();
      setBookings(data.results || data);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => { fetchBookings(); }, []);

  const handleAction = async (id, action) => {
    setActionLoading(id + action);
    try {
      if (action === "entry")  await bookingAPI.entry(id);
      if (action === "exit")   await bookingAPI.exit(id);
      if (action === "cancel") await bookingAPI.cancel(id);
      toast.success(`Booking ${action} successful!`);
      fetchBookings();
    } catch (err) {
      toast.error(err.response?.data?.detail || "Action failed");
    } finally {
      setActionLoading(null);
    }
  };

  if (loading) return (
    <div className="flex items-center justify-center min-h-[60vh]">
      <RiLoader4Line className="animate-spin text-primary-400 text-4xl" />
    </div>
  );

  return (
    <div className="max-w-4xl mx-auto px-4 py-10 animate-fade-in">
      <div className="mb-8">
        <h1 className="font-display font-bold text-3xl text-white">My Bookings</h1>
        <p className="text-slate-400 text-sm mt-1">{bookings.length} booking{bookings.length !== 1 ? "s" : ""} found</p>
      </div>

      {bookings.length === 0 ? (
        <div className="glass-card p-16 text-center">
          <div className="text-5xl mb-4">🅿️</div>
          <p className="text-slate-400">No bookings yet. <a href="/search" className="text-primary-400 underline">Find parking →</a></p>
        </div>
      ) : (
        <div className="space-y-4">
          {bookings.map((b, i) => (
            <motion.div key={b.id} initial={{ opacity: 0, x: -16 }}
              animate={{ opacity: 1, x: 0 }} transition={{ delay: i * 0.06 }}
              className="glass-card-hover p-5 space-y-4">

              {/* Header row */}
              <div className="flex items-start justify-between gap-3">
                <div className="flex items-center gap-3">
                  <div className="w-11 h-11 rounded-xl bg-gradient-to-br from-primary-600 to-accent-600
                                  flex items-center justify-center text-white text-xl shadow-glow-sm">
                    🅿️
                  </div>
                  <div>
                    <div className="font-semibold text-white text-sm">
                      {b.slot?.lot?.name || `Slot ${b.slot?.slot_number}`}
                    </div>
                    <div className="text-slate-500 text-xs font-mono">{b.id.slice(0, 8).toUpperCase()}</div>
                  </div>
                </div>
                <span className={`${STATUS_BADGE[b.status] || "badge"} badge flex items-center gap-1`}>
                  {STATUS_ICON[b.status]} {b.status}
                </span>
              </div>

              {/* Time & billing */}
              <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
                {[
                  { label: "Scheduled",  value: format(new Date(b.scheduled_start), "dd MMM, HH:mm") },
                  { label: "Duration",   value: `→ ${format(new Date(b.scheduled_end), "HH:mm")}` },
                  { label: "Estimated",  value: `₹${b.estimated_amount}` },
                  { label: "Final Bill", value: b.final_amount ? `₹${b.final_amount}` : "—" },
                ].map((item) => (
                  <div key={item.label} className="bg-white/5 rounded-xl p-3">
                    <div className="text-slate-500 text-xs mb-0.5">{item.label}</div>
                    <div className="text-white text-sm font-medium">{item.value}</div>
                  </div>
                ))}
              </div>

              {/* Refund */}
              {Number(b.refund_amount) > 0 && (
                <div className="flex items-center gap-2 text-sm text-success bg-success/10 border border-success/20 rounded-xl px-4 py-3">
                  <RiRefundLine />
                  Refund of <strong>₹{b.refund_amount}</strong> processed for unused time
                </div>
              )}

              {/* Actions */}
              <div className="flex items-center gap-2 pt-2 border-t border-white/8 flex-wrap">
                {b.status === "confirmed" && (
                  <button onClick={() => handleAction(b.id, "entry")}
                    disabled={!!actionLoading}
                    className="btn-primary text-xs px-4 py-2">
                    {actionLoading === b.id + "entry" ? <RiLoader4Line className="animate-spin" /> : "✅ Mark Entry"}
                  </button>
                )}
                {b.status === "active" && (
                  <button onClick={() => handleAction(b.id, "exit")}
                    disabled={!!actionLoading}
                    className="btn-primary text-xs px-4 py-2">
                    {actionLoading === b.id + "exit" ? <RiLoader4Line className="animate-spin" /> : "🚗 Mark Exit"}
                  </button>
                )}
                {["pending", "confirmed"].includes(b.status) && (
                  <button onClick={() => handleAction(b.id, "cancel")}
                    disabled={!!actionLoading}
                    className="btn-secondary text-xs px-4 py-2 border-danger/40 text-danger hover:bg-danger/10">
                    Cancel
                  </button>
                )}
              </div>
            </motion.div>
          ))}
        </div>
      )}
    </div>
  );
}
