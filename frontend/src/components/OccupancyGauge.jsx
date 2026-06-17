/**
 * OccupancyGauge — Animated circular occupancy gauge
 * Shows occupancy % with colour-coded bands:
 *   Green  0–40%
 *   Yellow 40–70%
 *   Red    70–100%
 */

import { useMemo } from "react";
import { motion } from "framer-motion";

const BAND_COLOR = (pct) => {
  if (pct < 40) return { stroke: "#22c55e", text: "text-emerald-400", glow: "rgba(34,197,94,0.3)" };
  if (pct < 70) return { stroke: "#f59e0b", text: "text-amber-400",   glow: "rgba(245,158,11,0.3)" };
  return          { stroke: "#ef4444", text: "text-red-400",    glow: "rgba(239,68,68,0.3)" };
};

export default function OccupancyGauge({
  occupancyRate = 0,  // 0–100
  totalSlots = 0,
  occupiedSlots = 0,
  size = 120,
  showLabels = true,
}) {
  const pct = Math.min(100, Math.max(0, occupancyRate));
  const color = BAND_COLOR(pct);

  // SVG arc calculation
  const radius = 44;
  const circumference = 2 * Math.PI * radius;
  const strokeDash = useMemo(
    () => (pct / 100) * circumference,
    [pct, circumference]
  );

  return (
    <div className="flex flex-col items-center gap-2">
      {/* Circular Gauge */}
      <div
        className="relative"
        style={{ width: size, height: size }}
      >
        <svg
          viewBox="0 0 100 100"
          width={size}
          height={size}
          style={{ transform: "rotate(-90deg)" }}
        >
          {/* Background track */}
          <circle
            cx="50" cy="50" r={radius}
            fill="none"
            stroke="rgba(255,255,255,0.08)"
            strokeWidth="10"
          />
          {/* Animated progress arc */}
          <motion.circle
            cx="50" cy="50" r={radius}
            fill="none"
            stroke={color.stroke}
            strokeWidth="10"
            strokeLinecap="round"
            strokeDasharray={circumference}
            initial={{ strokeDashoffset: circumference }}
            animate={{ strokeDashoffset: circumference - strokeDash }}
            transition={{ duration: 0.9, ease: "easeOut" }}
            style={{
              filter: `drop-shadow(0 0 6px ${color.glow})`,
            }}
          />
        </svg>

        {/* Center text */}
        <div className="absolute inset-0 flex flex-col items-center justify-center">
          <motion.span
            className={`font-bold leading-none ${color.text}`}
            style={{ fontSize: size * 0.22 }}
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            transition={{ delay: 0.3 }}
          >
            {pct.toFixed(0)}%
          </motion.span>
          {size >= 100 && (
            <span className="text-slate-500" style={{ fontSize: size * 0.10 }}>
              full
            </span>
          )}
        </div>
      </div>

      {/* Slot counts */}
      {showLabels && (
        <div className="flex gap-3 text-xs text-center">
          <div>
            <div className="text-white font-semibold">{totalSlots}</div>
            <div className="text-slate-500">Total</div>
          </div>
          <div className="w-px bg-white/10" />
          <div>
            <div className={`font-semibold ${color.text}`}>{occupiedSlots}</div>
            <div className="text-slate-500">Occupied</div>
          </div>
          <div className="w-px bg-white/10" />
          <div>
            <div className="text-emerald-400 font-semibold">
              {totalSlots - occupiedSlots}
            </div>
            <div className="text-slate-500">Free</div>
          </div>
        </div>
      )}
    </div>
  );
}
