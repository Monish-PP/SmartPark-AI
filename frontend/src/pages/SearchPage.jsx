import { useEffect, useState } from "react";
import { useDispatch, useSelector } from "react-redux";
import { motion, AnimatePresence } from "framer-motion";
import {
  RiSearchLine, RiMapPinLine, RiTimeLine, RiCarLine,
  RiMotorbikeLine, RiTruckLine, RiLoader4Line,
} from "react-icons/ri";
import { searchParking, setSearchParams } from "../store/slices/parkingSlice";
import ParkingCard from "../components/ParkingCard";
import LiveHeatmap from "../components/LiveHeatmap";

const VEHICLE_TYPES = [
  { value: "two_wheeler",  label: "Two Wheeler",   icon: <RiMotorbikeLine size={20} /> },
  { value: "four_wheeler", label: "Four Wheeler",  icon: <RiCarLine size={20} /> },
  { value: "heavy",        label: "Heavy Vehicle", icon: <RiTruckLine size={20} /> },
];

export default function SearchPage() {
  const dispatch = useDispatch();
  const { searchResults, searchLoading } = useSelector((s) => s.parking);

  const [form, setForm] = useState({
    vehicle_type: "four_wheeler",
    address: "",
    lat: "",
    lng: "",
    duration_hours: 2,
  });
  const [view, setView] = useState("list"); // "list" | "map"
  const [geocoding, setGeocoding] = useState(false);
  const [locationNote, setLocationNote] = useState("");

  useEffect(() => {
    if (!navigator.geolocation) {
      setLocationNote("Location access is unavailable in this browser.");
      return;
    }

    navigator.geolocation.getCurrentPosition(
      (position) => {
        const lat = position.coords.latitude;
        const lng = position.coords.longitude;

        setForm((f) => ({
          ...f,
          lat,
          lng,
          address: "Current location",
        }));

        const params = {
          vehicle_type: "four_wheeler",
          lat,
          lng,
          duration_hours: 2,
        };

        dispatch(setSearchParams(params));
        dispatch(searchParking(params));
        setView("map");
        setLocationNote("Showing nearby parking spots around your current location.");
      },
      () => {
        setLocationNote("We can still show available parking; use the search box to choose a destination.");
      },
      { enableHighAccuracy: true, timeout: 10000, maximumAge: 60000 }
    );
  }, [dispatch]);

  const geocodeAddress = async (address) => {
    if (!address) return;
    setGeocoding(true);
    try {
      const key = import.meta.env.VITE_GOOGLE_MAPS_KEY;
      const res = await fetch(
        `https://maps.googleapis.com/maps/api/geocode/json?address=${encodeURIComponent(address)}&key=${key}`
      );
      const data = await res.json();
      if (data.results?.[0]) {
        const { lat, lng } = data.results[0].geometry.location;
        setForm((f) => ({ ...f, lat, lng }));
        return { lat, lng };
      }
    } catch (e) {
      console.error("Geocoding failed:", e);
    } finally {
      setGeocoding(false);
    }
  };

  const handleSearch = async (e) => {
    e.preventDefault();
    let { lat, lng } = form;
    if (!lat || !lng) {
      const coords = await geocodeAddress(form.address);
      if (!coords) return;
      lat = coords.lat;
      lng = coords.lng;
    }
    const params = {
      vehicle_type: form.vehicle_type,
      lat, lng,
      duration_hours: form.duration_hours,
    };
    dispatch(setSearchParams(params));
    dispatch(searchParking(params));
  };

  return (
    <div className="max-w-7xl mx-auto px-4 py-10 animate-fade-in">
      {/* ── Search Form ─────────────────────────────────────────────── */}
      <div className="mb-8">
        <h1 className="font-display font-bold text-3xl text-white mb-1">
          Find Your <span className="text-gradient">Perfect Spot</span>
        </h1>
        <p className="text-slate-400 text-sm">AI recommends best parking based on your needs</p>
        {locationNote && (
          <p className="mt-2 text-xs text-primary-200">{locationNote}</p>
        )}
      </div>

      <form onSubmit={handleSearch} className="glass-card p-6 mb-8">
        <div className="grid sm:grid-cols-2 lg:grid-cols-4 gap-4">
          {/* Vehicle Type */}
          <div className="flex flex-col gap-2">
            <label className="text-xs text-slate-400 font-medium">Vehicle Type</label>
            <div className="flex gap-2">
              {VEHICLE_TYPES.map((v) => (
                <button
                  key={v.value}
                  type="button"
                  onClick={() => setForm((f) => ({ ...f, vehicle_type: v.value }))}
                  className={`flex-1 flex flex-col items-center gap-1 py-3 px-2 rounded-xl border text-xs font-medium transition-all duration-200
                    ${form.vehicle_type === v.value
                      ? "border-primary-500/60 bg-primary-500/15 text-primary-300"
                      : "border-white/10 bg-white/5 text-slate-400 hover:border-white/20"
                    }`}
                >
                  {v.icon}
                  <span className="hidden sm:block">{v.label.split(" ")[0]}</span>
                </button>
              ))}
            </div>
          </div>

          {/* Destination */}
          <div className="lg:col-span-2 flex flex-col gap-2">
            <label className="text-xs text-slate-400 font-medium">Destination</label>
            <div className="relative">
              <RiMapPinLine className="absolute left-3 top-1/2 -translate-y-1/2 text-slate-500" />
              <input
                className="input-field pl-9"
                placeholder="Enter location or landmark..."
                value={form.address}
                onChange={(e) => setForm((f) => ({ ...f, address: e.target.value }))}
                required
              />
              {geocoding && (
                <RiLoader4Line className="absolute right-3 top-1/2 -translate-y-1/2 text-primary-400 animate-spin" />
              )}
            </div>
          </div>

          {/* Duration */}
          <div className="flex flex-col gap-2">
            <label className="text-xs text-slate-400 font-medium">
              Duration: <span className="text-white font-semibold">{form.duration_hours}h</span>
            </label>
            <div className="relative flex items-center gap-3 h-[46px]">
              <RiTimeLine className="text-slate-500 shrink-0" />
              <input
                type="range" min={1} max={24} step={0.5}
                value={form.duration_hours}
                onChange={(e) => setForm((f) => ({ ...f, duration_hours: +e.target.value }))}
                className="w-full accent-primary-500 cursor-pointer"
              />
            </div>
          </div>
        </div>

        <div className="flex items-center justify-between mt-4 pt-4 border-t border-white/8">
          <div className="flex gap-2">
            {["list", "map"].map((v) => (
              <button
                key={v}
                type="button"
                onClick={() => setView(v)}
                className={`px-4 py-2 rounded-lg text-sm font-medium transition-all capitalize
                  ${view === v ? "bg-primary-500/20 text-primary-300 border border-primary-500/30"
                               : "text-slate-400 hover:text-white hover:bg-white/5"}`}
              >
                {v === "list" ? "📋 List" : "🗺️ Map"} View
              </button>
            ))}
          </div>
          <button type="submit" className="btn-primary" disabled={searchLoading}>
            {searchLoading
              ? <><RiLoader4Line className="animate-spin" /> Searching...</>
              : <><RiSearchLine /> Find Parking</>
            }
          </button>
        </div>
      </form>

      {/* ── Results ─────────────────────────────────────────────────── */}
      {view === "map" ? (
        <LiveHeatmap results={searchResults} />
      ) : (
        <div>
          {searchResults.length > 0 && (
            <div className="flex items-center justify-between mb-4">
              <h2 className="section-title text-xl">
                {searchResults.length} Spots Found
                <span className="text-sm font-normal text-slate-400 ml-2">
                  — ranked by AI score
                </span>
              </h2>
            </div>
          )}

          <AnimatePresence mode="popLayout">
            {searchLoading ? (
              <div className="grid sm:grid-cols-2 lg:grid-cols-3 gap-4">
                {Array.from({ length: 6 }).map((_, i) => (
                  <motion.div key={i} className="glass-card h-56 animate-pulse" />
                ))}
              </div>
            ) : searchResults.length > 0 ? (
              <motion.div
                className="grid sm:grid-cols-2 lg:grid-cols-3 gap-4"
                initial="hidden"
                animate="show"
                variants={{ show: { transition: { staggerChildren: 0.07 } } }}
              >
                {searchResults.map((lot, i) => (
                  <ParkingCard key={lot.lot_id} lot={lot} rank={i + 1}
                               duration={form.duration_hours}
                               vehicleType={form.vehicle_type} />
                ))}
              </motion.div>
            ) : (
              <div className="glass-card p-16 text-center">
                <div className="text-5xl mb-4">🅿️</div>
                <p className="text-slate-400">
                  Enter your destination and click <strong className="text-white">Find Parking</strong> to see AI recommendations
                </p>
              </div>
            )}
          </AnimatePresence>
        </div>
      )}
    </div>
  );
}
