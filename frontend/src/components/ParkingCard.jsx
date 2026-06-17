import { motion } from "framer-motion";
import { useNavigate } from "react-router-dom";
import {
  RiMapPinLine, RiStarFill, RiTimeLine,
  RiCarLine, RiCheckboxCircleLine, RiArrowRightLine,
  RiBrainLine,
} from "react-icons/ri";

const cardVariant = {
  hidden: { opacity: 0, y: 20 },
  show:   { opacity: 1, y: 0, transition: { duration: 0.35 } },
};

// Colour-coded AI score badge
const scoreColor = (score) => {
  if (score >= 0.75) return "badge-success";
  if (score >= 0.45) return "badge-warning";
  return "badge-danger";
};

const scoreLabel = (score) => {
  if (score >= 0.75) return "Excellent";
  if (score >= 0.45) return "Good";
  return "Fair";
};

export default function ParkingCard({ lot, rank, duration = 1, vehicleType }) {
  const navigate = useNavigate();
  const estimatedCost = lot.price_per_hour
    ? (lot.price_per_hour * duration).toFixed(0)
    : "—";

  return (
    <motion.div
      variants={cardVariant}
      whileHover={{ y: -4 }}
      className="glass-card-hover p-5 flex flex-col gap-4 cursor-pointer group relative"
      onClick={() => navigate(`/book/${lot.best_slot_id}`, { state: { lot, duration, vehicleType } })}
    >
      {/* Rank badge */}
      {rank <= 3 && (
        <div className="absolute -top-2 -left-2 w-7 h-7 rounded-full bg-gradient-to-br
                        from-primary-500 to-accent-600 flex items-center justify-center
                        text-white text-xs font-bold shadow-glow-sm">
          {rank}
        </div>
      )}

      {/* Header */}
      <div className="flex items-start justify-between gap-3">
        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-2 flex-wrap">
            <h3 className="font-semibold text-white text-base truncate group-hover:text-primary-300 transition-colors">
              {lot.lot_name}
            </h3>
            {lot.occupancy_rate != null && (
              <span className="inline-flex items-center gap-1 px-1.5 py-0.5 rounded bg-primary-500/10 border border-primary-500/20 text-[10px] text-primary-300 uppercase font-semibold">
                <span className="w-1.5 h-1.5 rounded-full bg-emerald-500 animate-pulse" />
                Live
              </span>
            )}
          </div>
          <div className="flex items-center gap-1 text-slate-400 text-xs mt-1">
            <RiMapPinLine className="shrink-0" />
            <span className="truncate">{lot.address}</span>
          </div>
        </div>
        {lot.is_verified && (
          <RiCheckboxCircleLine className="text-success shrink-0 mt-0.5" title="Verified Lot" />
        )}
      </div>

      {/* AI Score */}
      {lot.ai_score != null && (
        <div className="flex items-center gap-2">
          <RiBrainLine className="text-primary-400 text-sm" />
          <span className="text-xs text-slate-400">AI Score</span>
          <span className={scoreColor(lot.ai_score)}>
            {scoreLabel(lot.ai_score)} ({(lot.ai_score * 100).toFixed(0)}/100)
          </span>
        </div>
      )}

      {/* Occupancy bar */}
      {lot.occupancy_rate != null && (
        <div className="space-y-1">
          <div className="flex justify-between text-xs text-slate-400">
            <span>Occupancy Rate</span>
            <span className="font-semibold text-white">{(lot.occupancy_rate * 100).toFixed(0)}%</span>
          </div>
          <div className="w-full bg-white/5 rounded-full h-1.5 overflow-hidden">
            <div
              className={`h-full rounded-full transition-all duration-500 ${
                lot.occupancy_rate < 0.40 ? "bg-emerald-500" : lot.occupancy_rate < 0.70 ? "bg-amber-500" : "bg-red-500"
              }`}
              style={{ width: `${(lot.occupancy_rate * 100).toFixed(0)}%` }}
            />
          </div>
        </div>
      )}

      {/* Metrics row */}
      <div className="grid grid-cols-3 gap-2">
        <div className="bg-white/5 rounded-xl p-3 text-center">
          <div className="text-white font-semibold text-sm">
            {lot.distance_km != null ? `${lot.distance_km.toFixed(1)} km` : "—"}
          </div>
          <div className="text-slate-500 text-xs mt-0.5">Distance</div>
        </div>
        <div className="bg-white/5 rounded-xl p-3 text-center">
          <div className="text-white font-semibold text-sm">
            ₹{lot.price_per_hour?.toFixed(0) ?? "—"}/hr
          </div>
          <div className="text-slate-500 text-xs mt-0.5">Price</div>
        </div>
        <div className="bg-white/5 rounded-xl p-3 text-center">
          <div className={`font-semibold text-sm ${lot.available_slots > 0 ? "text-success" : "text-danger"}`}>
            {lot.available_slots ?? "—"}
          </div>
          <div className="text-slate-500 text-xs mt-0.5">Free Slots</div>
        </div>
      </div>

      {/* Footer */}
      <div className="flex items-center justify-between pt-2 border-t border-white/8">
        <div className="flex items-center gap-3">
          {lot.avg_rating > 0 && (
            <span className="flex items-center gap-1 text-xs text-slate-400">
              <RiStarFill className="text-warning" />
              {lot.avg_rating.toFixed(1)}
            </span>
          )}
          <span className="flex items-center gap-1 text-xs text-slate-400">
            <RiTimeLine />
            Est. ₹{estimatedCost} for {duration}h
          </span>
        </div>
        <RiArrowRightLine className="text-primary-500 group-hover:translate-x-1 transition-transform duration-200" />
      </div>
    </motion.div>
  );
}
