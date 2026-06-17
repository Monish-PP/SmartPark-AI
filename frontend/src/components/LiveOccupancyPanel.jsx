/**
 * LiveOccupancyPanel — Real-time slot grid with Supabase subscription
 *
 * Shows:
 *   - Grid of slot squares (green=free, red=occupied)
 *   - Live counts header
 *   - Last updated timestamp with animated live indicator
 *   - Auto-updates via Supabase Broadcast channel
 */

import { useEffect, useState, useRef } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { RiWifiLine, RiWifiOffLine } from "react-icons/ri";
import { subscribeToOccupancy, unsubscribe } from "../services/realtimeService";
import { occupancyAPI } from "../services/api";
import OccupancyGauge from "./OccupancyGauge";
import OccupancyTrendChart from "./OccupancyTrendChart";

const fmtTime = (ts) => {
  if (!ts) return "—";
  try {
    return new Date(ts).toLocaleTimeString();
  } catch {
    return ts;
  }
};

const SLOT_COLOR = (isOccupied) =>
  isOccupied
    ? "bg-red-500/70 border-red-400/50"
    : "bg-emerald-500/70 border-emerald-400/50";

export default function LiveOccupancyPanel({ parkingLotId, parkingLotName }) {
  const [snapshot, setSnapshot] = useState(null);
  const [history, setHistory]   = useState([]);
  const [loading, setLoading]   = useState(true);
  const [connected, setConnected] = useState(false);
  const subRef = useRef(null);

  // ── Initial Data Fetch ────────────────────────────────────────────────────
  useEffect(() => {
    if (!parkingLotId) return;

    occupancyAPI.getForLot(parkingLotId)
      .then(({ data }) => {
        if (data.snapshot) setSnapshot(data.snapshot);
        if (data.history)  setHistory(data.history);
      })
      .catch(console.error)
      .finally(() => setLoading(false));
  }, [parkingLotId]);

  // ── Supabase Realtime Subscription ───────────────────────────────────────
  useEffect(() => {
    if (!parkingLotId) return;

    const sub = subscribeToOccupancy(parkingLotId, (payload) => {
      setConnected(true);
      setSnapshot((prev) => ({
        ...prev,
        ...payload,
        slot_states: payload.slot_states ?? prev?.slot_states ?? {},
        edge_timestamp: payload.timestamp,
      }));
    });
    subRef.current = sub;

    return () => {
      if (subRef.current) unsubscribe(subRef.current);
      setConnected(false);
    };
  }, [parkingLotId]);

  if (loading) {
    return (
      <div className="glass-card p-6 animate-pulse">
        <div className="h-4 bg-white/10 rounded w-1/3 mb-4" />
        <div className="grid grid-cols-6 gap-2">
          {Array.from({ length: 18 }).map((_, i) => (
            <div key={i} className="h-8 bg-white/8 rounded" />
          ))}
        </div>
      </div>
    );
  }

  if (!snapshot) {
    return (
      <div className="glass-card p-6 text-center text-slate-500 text-sm">
        <RiWifiOffLine className="text-2xl mx-auto mb-2 opacity-40" />
        No occupancy data — edge service not yet connected
      </div>
    );
  }

  const slotStates = snapshot.slot_states ?? {};
  const slotEntries = Object.entries(slotStates);

  return (
    <div className="glass-card p-5 space-y-5">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h3 className="font-semibold text-white text-sm">
            Live Occupancy
            {parkingLotName && (
              <span className="text-slate-400 font-normal ml-1.5">— {parkingLotName}</span>
            )}
          </h3>
          <p className="text-xs text-slate-500 mt-0.5">
            Updated: {fmtTime(snapshot.edge_timestamp ?? snapshot.received_at)}
          </p>
        </div>
        {/* Live indicator */}
        <div className={`flex items-center gap-1.5 text-xs ${connected ? "text-emerald-400" : "text-slate-500"}`}>
          {connected
            ? <><div className="w-2 h-2 rounded-full bg-emerald-400 animate-pulse" /> LIVE</>
            : <><RiWifiOffLine /> Offline</>
          }
        </div>
      </div>

      {/* Gauge + Slot Grid row */}
      <div className="flex flex-col sm:flex-row gap-6 items-center">
        {/* Gauge */}
        <OccupancyGauge
          occupancyRate={snapshot.occupancy_rate ?? 0}
          totalSlots={snapshot.total_slots ?? 0}
          occupiedSlots={snapshot.occupied_slots ?? 0}
          size={110}
        />

        {/* Slot grid */}
        {slotEntries.length > 0 ? (
          <div className="flex-1">
            <div className="text-xs text-slate-400 mb-2">
              Individual Slots ({slotEntries.length})
            </div>
            <div
              className="grid gap-1.5"
              style={{
                gridTemplateColumns: `repeat(${Math.min(slotEntries.length, 8)}, minmax(0, 1fr))`,
              }}
            >
              <AnimatePresence>
                {slotEntries.map(([slotId, isOccupied]) => (
                  <motion.div
                    key={slotId}
                    layout
                    initial={{ scale: 0.8, opacity: 0 }}
                    animate={{ scale: 1, opacity: 1 }}
                    title={`Slot ${slotId}: ${isOccupied ? "Occupied" : "Free"}`}
                    className={`
                      rounded border text-center text-xs font-medium py-1 px-0.5
                      cursor-default transition-colors duration-500
                      ${SLOT_COLOR(isOccupied)}
                    `}
                  >
                    {slotId}
                  </motion.div>
                ))}
              </AnimatePresence>
            </div>
            {/* Slot legend */}
            <div className="flex gap-4 mt-2 text-xs text-slate-500">
              <span className="flex items-center gap-1">
                <div className="w-2 h-2 rounded-sm bg-emerald-500" /> Free
              </span>
              <span className="flex items-center gap-1">
                <div className="w-2 h-2 rounded-sm bg-red-500" /> Occupied
              </span>
            </div>
          </div>
        ) : (
          <div className="flex-1 text-slate-500 text-xs text-center">
            Slot-level data unavailable<br />
            (edge running in count mode)
          </div>
        )}
      </div>

      {/* Trend chart */}
      {history.length > 0 && (
        <OccupancyTrendChart
          history={history}
          height={90}
          title="24h Occupancy Trend"
        />
      )}
    </div>
  );
}
