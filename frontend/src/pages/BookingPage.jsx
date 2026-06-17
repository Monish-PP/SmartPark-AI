import { useState } from "react";
import { useLocation, useNavigate } from "react-router-dom";
import { motion } from "framer-motion";
import { bookingAPI } from "../services/api";
import {
  RiMapPinLine, RiTimeLine, RiMoneyDollarCircleLine,
  RiCarLine, RiCheckboxCircleLine, RiLoader4Line,
  RiCalendarLine,
} from "react-icons/ri";
import toast from "react-hot-toast";
import { format, addHours } from "date-fns";

export default function BookingPage() {
  const { state } = useLocation();
  const navigate = useNavigate();
  const { lot, duration, vehicleType } = state || {};

  const [loading, setLoading] = useState(false);
  const [step, setStep] = useState(1); // 1=summary, 2=payment

  const startTime = new Date();
  const endTime = addHours(startTime, duration || 1);
  const estimatedCost = lot
    ? (lot.price_per_hour * (duration || 1)).toFixed(2)
    : "0";

  const loadRazorpay = () =>
    new Promise((resolve) => {
      if (window.Razorpay) return resolve(true);
      const script = document.createElement("script");
      script.src = "https://checkout.razorpay.com/v1/checkout.js";
      script.onload = () => resolve(true);
      script.onerror = () => resolve(false);
      document.body.appendChild(script);
    });

  const handleBook = async () => {
    setLoading(true);
    try {
      const { data } = await bookingAPI.create({
        slot: lot?.best_slot_id,
        vehicle: null, // Select from user's vehicles in production
        scheduled_start: startTime.toISOString(),
        scheduled_end: endTime.toISOString(),
        ai_score: lot?.ai_score,
        distance_km: lot?.distance_km,
      });

      const loaded = await loadRazorpay();
      if (!loaded) { toast.error("Payment gateway failed to load."); return; }

      const options = {
        key: import.meta.env.VITE_RAZORPAY_KEY,
        amount: data.amount,
        currency: data.currency,
        name: "SmartPark AI",
        description: `Parking at ${lot?.lot_name}`,
        order_id: data.razorpay_order_id,
        handler: async (response) => {
          await bookingAPI.verifyPayment({
            razorpay_order_id: response.razorpay_order_id,
            razorpay_payment_id: response.razorpay_payment_id,
            razorpay_signature: response.razorpay_signature,
          });
          toast.success("Booking confirmed! 🎉");
          navigate("/bookings");
        },
        prefill: { name: "", email: "", contact: "" },
        theme: { color: "#118af5" },
      };

      new window.Razorpay(options).open();
    } catch (err) {
      toast.error(err.response?.data?.detail || "Booking failed. Please try again.");
    } finally {
      setLoading(false);
    }
  };

  if (!lot) {
    return (
      <div className="max-w-lg mx-auto px-4 py-20 text-center">
        <div className="text-4xl mb-4">🅿️</div>
        <p className="text-slate-400">No parking lot selected. <a href="/search" className="text-primary-400 underline">Search again</a></p>
      </div>
    );
  }

  return (
    <div className="max-w-2xl mx-auto px-4 py-10 animate-fade-in">
      <div className="mb-8">
        <h1 className="font-display font-bold text-3xl text-white mb-1">Confirm Booking</h1>
        <p className="text-slate-400 text-sm">Review your parking details before payment</p>
      </div>

      <motion.div className="glass-card p-6 space-y-5">
        {/* Lot info */}
        <div className="flex items-start gap-4 pb-5 border-b border-white/8">
          <div className="w-14 h-14 rounded-xl bg-gradient-to-br from-primary-600 to-accent-600
                          flex items-center justify-center text-2xl shadow-glow-sm text-white shrink-0">
            🅿️
          </div>
          <div>
            <h2 className="font-semibold text-white text-lg">{lot.lot_name}</h2>
            <div className="flex items-center gap-1 text-slate-400 text-sm mt-1">
              <RiMapPinLine /> {lot.address}
            </div>
            {lot.is_verified && (
              <span className="badge-success mt-2 inline-flex">
                <RiCheckboxCircleLine /> Verified Lot
              </span>
            )}
          </div>
        </div>

        {/* Booking details */}
        <div className="grid grid-cols-2 gap-4">
          {[
            { icon: <RiCalendarLine />, label: "Start",    value: format(startTime, "dd MMM yyyy, hh:mm a") },
            { icon: <RiCalendarLine />, label: "End",      value: format(endTime, "dd MMM yyyy, hh:mm a") },
            { icon: <RiTimeLine />,     label: "Duration", value: `${duration} hour${duration > 1 ? "s" : ""}` },
            { icon: <RiCarLine />,      label: "Vehicle",  value: vehicleType?.replace("_", " ") || "—" },
          ].map((item) => (
            <div key={item.label} className="bg-white/5 rounded-xl p-3">
              <div className="flex items-center gap-1.5 text-xs text-slate-400 mb-1">
                {item.icon} {item.label}
              </div>
              <div className="text-white font-medium text-sm capitalize">{item.value}</div>
            </div>
          ))}
        </div>

        {/* Pricing breakdown */}
        <div className="bg-primary-500/10 border border-primary-500/25 rounded-xl p-4 space-y-2">
          <div className="flex justify-between text-sm">
            <span className="text-slate-400">Rate</span>
            <span className="text-white">₹{lot.price_per_hour}/hr</span>
          </div>
          <div className="flex justify-between text-sm">
            <span className="text-slate-400">Duration</span>
            <span className="text-white">{duration}h</span>
          </div>
          <div className="border-t border-primary-500/20 pt-2 flex justify-between font-semibold">
            <span className="text-white">Estimated Total</span>
            <div className="flex items-center gap-1 text-primary-300 text-lg">
              <RiMoneyDollarCircleLine />
              ₹{estimatedCost}
            </div>
          </div>
          <p className="text-xs text-slate-500 pt-1">
            ✦ Unused time will be auto-refunded after exit.
          </p>
        </div>

        {/* AI Info */}
        {lot.ai_score && (
          <div className="flex items-center gap-3 text-sm text-slate-400 bg-white/5 rounded-xl p-3">
            <span className="text-lg">🤖</span>
            <span>AI confidence: <strong className="text-primary-300">{(lot.ai_score * 100).toFixed(0)}/100</strong>
              &nbsp;· Distance: <strong className="text-white">{lot.distance_km?.toFixed(1)} km</strong></span>
          </div>
        )}

        <button
          onClick={handleBook}
          disabled={loading}
          className="btn-primary w-full justify-center text-base py-4"
        >
          {loading
            ? <><RiLoader4Line className="animate-spin" /> Processing...</>
            : <>🔒 Pay ₹{estimatedCost} & Confirm Booking</>
          }
        </button>
        <p className="text-center text-xs text-slate-500">
          Secured by Razorpay · 256-bit SSL encryption
        </p>
      </motion.div>
    </div>
  );
}
