import { useEffect, useState } from "react";
import { motion } from "framer-motion";
import { analyticsAPI } from "../services/api";
import {
  RiMoneyDollarCircleLine, RiParkingBoxLine, RiBarChartBoxLine,
  RiStarFill, RiRefreshLine, RiLoader4Line, RiSensorLine,
} from "react-icons/ri";
import {
  Chart as ChartJS, CategoryScale, LinearScale, BarElement,
  LineElement, PointElement, Title, Tooltip, Legend, Filler,
} from "chart.js";
import { Bar, Line } from "react-chartjs-2";
import LiveOccupancyPanel from "../components/LiveOccupancyPanel";

ChartJS.register(
  CategoryScale, LinearScale, BarElement, LineElement,
  PointElement, Title, Tooltip, Legend, Filler
);

const CHART_OPTS = {
  responsive: true,
  plugins: { legend: { display: false }, tooltip: { mode: "index" } },
  scales: {
    x: { grid: { color: "rgba(255,255,255,0.05)" }, ticks: { color: "#94a3b8", font: { size: 11 } } },
    y: { grid: { color: "rgba(255,255,255,0.05)" }, ticks: { color: "#94a3b8", font: { size: 11 } } },
  },
};

export default function OwnerDashboard() {
  const [data, setData] = useState(null);
  const [period, setPeriod] = useState("week");
  const [loading, setLoading] = useState(true);

  const fetchData = async () => {
    setLoading(true);
    try {
      const { data: res } = await analyticsAPI.ownerDashboard(period);
      setData(res);
    } catch (e) {
      console.error(e);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => { fetchData(); }, [period]);

  if (loading) return (
    <div className="flex items-center justify-center min-h-[60vh]">
      <RiLoader4Line className="animate-spin text-primary-400 text-4xl" />
    </div>
  );

  const revenueChart = {
    labels: data?.daily_revenue?.map((d) => d.date.slice(5)) || [],
    datasets: [{
      data: data?.daily_revenue?.map((d) => d.revenue) || [],
      backgroundColor: "rgba(41,168,255,0.25)",
      borderColor: "#29a8ff",
      borderWidth: 2,
      borderRadius: 6,
      fill: true,
      tension: 0.4,
    }],
  };

  const stats = [
    { label: "Total Revenue", value: `₹${Number(data?.total_revenue || 0).toLocaleString()}`, icon: <RiMoneyDollarCircleLine />, color: "text-primary-400" },
    { label: "Your Earnings",  value: `₹${Number(data?.owner_earnings || 0).toLocaleString()}`, icon: <RiMoneyDollarCircleLine />, color: "text-success" },
    { label: "Total Bookings", value: data?.total_bookings ?? 0, icon: <RiParkingBoxLine />, color: "text-accent-400" },
    { label: "Platform Fee",   value: `₹${Number(data?.platform_commission || 0).toLocaleString()}`, icon: <RiBarChartBoxLine />, color: "text-warning" },
  ];

  return (
    <div className="max-w-7xl mx-auto px-4 py-10 animate-fade-in space-y-8">
      {/* Header */}
      <div className="flex items-center justify-between flex-wrap gap-4">
        <div>
          <h1 className="font-display font-bold text-3xl text-white">Owner Dashboard</h1>
          <p className="text-slate-400 text-sm mt-1">Track earnings, occupancy, and demand forecasts</p>
        </div>
        <div className="flex items-center gap-2">
          {["week", "month", "year"].map((p) => (
            <button key={p} onClick={() => setPeriod(p)}
              className={`px-4 py-2 rounded-lg text-sm font-medium capitalize transition-all
                ${period === p ? "bg-primary-500/20 text-primary-300 border border-primary-500/30"
                               : "text-slate-400 hover:text-white hover:bg-white/5"}`}>
              {p}
            </button>
          ))}
          <button onClick={fetchData} className="btn-ghost ml-2">
            <RiRefreshLine />
          </button>
        </div>
      </div>

      {/* Stat Cards */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
        {stats.map((s, i) => (
          <motion.div key={s.label} initial={{ opacity: 0, y: 16 }}
            animate={{ opacity: 1, y: 0 }} transition={{ delay: i * 0.08 }}
            className="stat-card">
            <div className={`text-2xl ${s.color}`}>{s.icon}</div>
            <div className="font-display font-bold text-2xl text-white">{s.value}</div>
            <div className="text-slate-400 text-xs">{s.label}</div>
          </motion.div>
        ))}
      </div>

      {/* Revenue Chart */}
      <div className="glass-card p-6">
        <h2 className="section-title text-lg mb-4">Daily Revenue</h2>
        <Line data={revenueChart} options={CHART_OPTS} height={80} />
      </div>

      {/* Lot Cards */}
      <div>
        <h2 className="section-title text-lg mb-4">Your Parking Lots</h2>
        <div className="grid md:grid-cols-2 gap-4">
          {(data?.lots || []).map((lot) => (
            <div key={lot.lot_id} className="glass-card-hover p-5 space-y-4">
              <div className="flex items-start justify-between">
                <div>
                  <h3 className="font-semibold text-white">{lot.lot_name}</h3>
                  <p className="text-slate-400 text-xs mt-0.5">{lot.total_slots} total slots</p>
                </div>
                <div className="text-right">
                  <div className="text-primary-300 font-bold">₹{lot.revenue?.toFixed(0) || 0}</div>
                  <div className="text-slate-500 text-xs">revenue</div>
                </div>
              </div>

              {/* Occupancy bar */}
              <div>
                <div className="flex justify-between text-xs text-slate-400 mb-1.5">
                  <span>Occupancy</span>
                  <span>{(lot.occupancy_rate * 100).toFixed(0)}%</span>
                </div>
                <div className="h-2 bg-white/8 rounded-full overflow-hidden">
                  <motion.div
                    initial={{ width: 0 }}
                    animate={{ width: `${lot.occupancy_rate * 100}%` }}
                    transition={{ duration: 0.8 }}
                    className={`h-full rounded-full ${lot.occupancy_rate > 0.8 ? "bg-danger"
                      : lot.occupancy_rate > 0.5 ? "bg-warning" : "bg-success"}`}
                  />
                </div>
                <div className="flex justify-between text-xs text-slate-500 mt-1">
                  <span>{lot.occupied_slots} occupied</span>
                  <span>{lot.total_slots - lot.occupied_slots} free</span>
                </div>
              </div>

              {/* Metrics row */}
              <div className="flex items-center gap-4 text-xs text-slate-400 pt-2 border-t border-white/8">
                <span>{lot.bookings_count} bookings</span>
                {lot.avg_rating > 0 && (
                  <span className="flex items-center gap-1">
                    <RiStarFill className="text-warning" /> {lot.avg_rating.toFixed(1)}
                  </span>
                )}
              </div>

              {/* Demand forecast mini-chart */}
              {lot.demand_forecast_24h?.length > 0 && (
                <div>
                  <div className="text-xs text-slate-400 mb-2">4-Hour Demand Forecast</div>
                  <Bar
                    data={{
                      labels: lot.demand_forecast_24h.map((_, i) => `+${(i + 1) * 0.5}h`),
                      datasets: [{
                        data: lot.demand_forecast_24h.map((d) => (d.predicted_occupancy_rate * 100).toFixed(0)),
                        backgroundColor: lot.demand_forecast_24h.map((d) =>
                          d.demand_level === "high"   ? "rgba(239,68,68,0.6)"
                          : d.demand_level === "medium" ? "rgba(245,158,11,0.6)"
                          : "rgba(34,197,94,0.6)"
                        ),
                        borderRadius: 4,
                      }],
                    }}
                    options={{ ...CHART_OPTS, scales: { x: CHART_OPTS.scales.x, y: { ...CHART_OPTS.scales.y, max: 100 } } }}
                    height={80}
                  />
                </div>
              )}

              {/* ── Live Occupancy Panel (Edge AI) ── */}
              <div className="pt-2 border-t border-white/8">
                <div className="flex items-center gap-2 mb-3">
                  <RiSensorLine className="text-primary-400" />
                  <span className="text-xs font-medium text-slate-300">Edge AI Live Data</span>
                </div>
                <LiveOccupancyPanel
                  parkingLotId={lot.lot_id}
                  parkingLotName={lot.lot_name}
                />
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
