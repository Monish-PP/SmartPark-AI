import { useEffect, useState } from "react";
import { motion } from "framer-motion";
import { analyticsAPI, occupancyAPI } from "../services/api";
import {
  RiAdminLine, RiMoneyDollarCircleLine, RiGroupLine,
  RiShieldCheckLine, RiAlertLine, RiLoader4Line,
  RiCamera3Line, RiParkingBoxLine, RiDashboardLine,
} from "react-icons/ri";
import { Bar, Doughnut } from "react-chartjs-2";
import {
  Chart as ChartJS, CategoryScale, LinearScale, BarElement,
  ArcElement, Title, Tooltip, Legend,
} from "chart.js";
import LiveHeatmap from "../components/LiveHeatmap";
import OccupancyTrendChart from "../components/OccupancyTrendChart";

ChartJS.register(CategoryScale, LinearScale, BarElement, ArcElement, Title, Tooltip, Legend);

export default function AdminPanel() {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [activeTab, setActiveTab] = useState("overview");

  const [occupancyData, setOccupancyData] = useState(null);
  const [occupancyLoading, setOccupancyLoading] = useState(true);

  useEffect(() => {
    analyticsAPI.adminAnalytics()
      .then(({ data: res }) => setData(res))
      .finally(() => setLoading(false));

    occupancyAPI.getAll()
      .then(({ data: res }) => setOccupancyData(res))
      .finally(() => setOccupancyLoading(false));
  }, []);

  if (loading) return (
    <div className="flex items-center justify-center min-h-[60vh]">
      <RiLoader4Line className="animate-spin text-primary-400 text-4xl" />
    </div>
  );

  const stats = [
    { label: "Platform Revenue",   value: `₹${Number(data?.total_revenue_30d || 0).toLocaleString()}`,   icon: <RiMoneyDollarCircleLine />, color: "from-primary-600 to-primary-800" },
    { label: "Commission Earned",  value: `₹${Number(data?.platform_commission_30d || 0).toLocaleString()}`, icon: <RiAdminLine />, color: "from-accent-600 to-accent-800" },
    { label: "Total Bookings",     value: data?.total_bookings_30d ?? 0,  icon: <RiShieldCheckLine />, color: "from-emerald-600 to-emerald-800" },
    { label: "New Users",          value: data?.new_users_30d ?? 0,       icon: <RiGroupLine />, color: "from-amber-600 to-amber-800" },
    { label: "New Owners",         value: data?.new_owners_30d ?? 0,      icon: <RiGroupLine />, color: "from-cyan-600 to-cyan-800" },
    { label: "Fraud Events",       value: data?.fraud_events_30d ?? 0,    icon: <RiAlertLine />, color: "from-rose-600 to-danger" },
  ];

  const topLotsChart = {
    labels: (data?.top_earning_lots || []).slice(0, 8).map((l) => l.slot__lot__name?.slice(0, 15)),
    datasets: [{
      label: "Revenue (₹)",
      data: (data?.top_earning_lots || []).slice(0, 8).map((l) => l.revenue),
      backgroundColor: "rgba(41,168,255,0.7)",
      borderRadius: 6,
    }],
  };

  const userSplitChart = {
    labels: ["Regular Users", "Owners"],
    datasets: [{
      data: [data?.new_users_30d || 0, data?.new_owners_30d || 0],
      backgroundColor: ["rgba(41,168,255,0.8)", "rgba(139,92,246,0.8)"],
      borderColor: ["#29a8ff", "#8b5cf6"],
      borderWidth: 2,
    }],
  };

  const TABS = [
    { id: "overview", label: "Overview" },
    { id: "lots",     label: "Top Lots" },
    { id: "heatmap",  label: "Live Heatmap" },
    { id: "occupancy", label: "Occupancy" },
  ];

  return (
    <div className="max-w-7xl mx-auto px-4 py-10 animate-fade-in space-y-8">
      {/* Header */}
      <div className="flex items-start justify-between flex-wrap gap-4">
        <div>
          <h1 className="font-display font-bold text-3xl text-white">Admin Console</h1>
          <p className="text-slate-400 text-sm mt-1">Platform-wide analytics · Last 30 days</p>
        </div>
        {data?.fraud_events_30d > 0 && (
          <div className="badge-danger text-sm px-3 py-2 animate-pulse-glow">
            <RiAlertLine /> {data.fraud_events_30d} Fraud Alerts
          </div>
        )}
      </div>

      {/* Stat cards */}
      <div className="grid grid-cols-2 lg:grid-cols-3 gap-4">
        {stats.map((s, i) => (
          <motion.div key={s.label}
            initial={{ opacity: 0, y: 16 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: i * 0.06 }}
            className="glass-card p-5 relative overflow-hidden group">
            <div className={`absolute inset-0 bg-gradient-to-br ${s.color} opacity-10 group-hover:opacity-15 transition-opacity`} />
            <div className="relative z-10 flex flex-col gap-2">
              <div className="text-2xl text-white opacity-70">{s.icon}</div>
              <div className="font-display font-bold text-2xl text-white">{s.value}</div>
              <div className="text-slate-400 text-xs">{s.label}</div>
            </div>
          </motion.div>
        ))}
      </div>

      {/* Tabs */}
      <div className="flex gap-2 border-b border-white/8 pb-0">
        {TABS.map((tab) => (
          <button key={tab.id} onClick={() => setActiveTab(tab.id)}
            className={`px-5 py-3 text-sm font-medium transition-all border-b-2 -mb-px
              ${activeTab === tab.id
                ? "border-primary-500 text-primary-300"
                : "border-transparent text-slate-400 hover:text-white"}`}>
            {tab.label}
          </button>
        ))}
      </div>

      {/* Tab content */}
      {activeTab === "overview" && (
        <div className="grid md:grid-cols-3 gap-6">
          <div className="md:col-span-2 glass-card p-6">
            <h2 className="section-title text-lg mb-4">Top Earning Lots (30d)</h2>
            {topLotsChart.labels?.length > 0
              ? <Bar data={topLotsChart} options={{ responsive: true, plugins: { legend: { display: false } } }} height={120} />
              : <div className="text-slate-500 text-sm text-center py-12">No data yet</div>
            }
          </div>
          <div className="glass-card p-6 flex flex-col">
            <h2 className="section-title text-lg mb-4">User Distribution</h2>
            <div className="flex-1 flex items-center justify-center">
              <Doughnut data={userSplitChart}
                options={{ plugins: { legend: { position: "bottom", labels: { color: "#94a3b8", padding: 16 } } } }} />
            </div>
          </div>
        </div>
      )}

      {activeTab === "lots" && (
        <div className="glass-card overflow-hidden">
          <div className="p-5 border-b border-white/8">
            <h2 className="section-title text-lg">Top Earning Parking Lots</h2>
          </div>
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b border-white/8">
                  {["#", "Lot Name", "Revenue", "Bookings"].map((h) => (
                    <th key={h} className="px-5 py-3 text-left text-slate-400 font-medium">{h}</th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {(data?.top_earning_lots || []).map((lot, i) => (
                  <tr key={lot.slot__lot__id} className="border-b border-white/5 hover:bg-white/5 transition-colors">
                    <td className="px-5 py-4 text-slate-500">{i + 1}</td>
                    <td className="px-5 py-4 text-white font-medium">{lot.slot__lot__name || "—"}</td>
                    <td className="px-5 py-4 text-primary-300 font-semibold">₹{Number(lot.revenue || 0).toLocaleString()}</td>
                    <td className="px-5 py-4 text-slate-300">{lot.bookings}</td>
                  </tr>
                ))}
                {!data?.top_earning_lots?.length && (
                  <tr><td colSpan={4} className="px-5 py-12 text-center text-slate-500">No data yet</td></tr>
                )}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {activeTab === "heatmap" && <LiveHeatmap />}

      {activeTab === "occupancy" && (
        <div className="space-y-6">
          {/* Occupancy stats summary */}
          <div className="grid grid-cols-2 md:grid-cols-5 gap-4">
            {[
              { label: "Edge Lots", value: occupancyData?.summary?.total_lots ?? 0, icon: <RiCamera3Line />, color: "from-cyan-600 to-cyan-800" },
              { label: "Total Slots", value: occupancyData?.summary?.total_slots ?? 0, icon: <RiParkingBoxLine />, color: "from-primary-600 to-primary-800" },
              { label: "Occupied Slots", value: occupancyData?.summary?.total_occupied ?? 0, icon: <RiDashboardLine />, color: "from-rose-600 to-danger" },
              { label: "Available Slots", value: occupancyData?.summary?.total_available ?? 0, icon: <RiShieldCheckLine />, color: "from-emerald-600 to-emerald-800" },
              { label: "Platform Occ. Rate", value: `${occupancyData?.summary?.platform_occupancy_rate ?? 0}%`, icon: <RiAdminLine />, color: "from-amber-600 to-amber-800" },
            ].map((s) => (
              <div key={s.label} className="glass-card p-4 relative overflow-hidden group">
                <div className={`absolute inset-0 bg-gradient-to-br ${s.color} opacity-10`} />
                <div className="relative z-10">
                  <div className="text-xl text-white opacity-70 mb-1">{s.icon}</div>
                  <div className="font-display font-bold text-xl text-white">{s.value}</div>
                  <div className="text-slate-400 text-xs mt-0.5">{s.label}</div>
                </div>
              </div>
            ))}
          </div>

          <div className="grid md:grid-cols-3 gap-6">
            {/* Trend Chart */}
            <div className="md:col-span-2 glass-card p-6">
              <h2 className="section-title text-lg mb-4">Platform Occupancy Trend (48h)</h2>
              {occupancyLoading ? (
                <div className="flex items-center justify-center h-48">
                  <RiLoader4Line className="animate-spin text-primary-400 text-3xl" />
                </div>
              ) : (
                <OccupancyTrendChart history={occupancyData?.history || []} height={200} title="Average Occupancy Rate" />
              )}
            </div>

            {/* Lot Summary list */}
            <div className="glass-card p-6 flex flex-col">
              <h2 className="section-title text-lg mb-4">Live Edge Lots</h2>
              <div className="flex-1 overflow-y-auto max-h-[300px] space-y-3 pr-1">
                {(occupancyData?.lots || []).map((lot) => {
                  const rate = lot.occupancy_rate || 0;
                  const color = rate < 40 ? "bg-emerald-500" : rate < 70 ? "bg-amber-500" : "bg-red-500";
                  return (
                    <div key={lot.id} className="flex items-center justify-between p-3 rounded-xl bg-white/5 border border-white/5">
                      <div className="min-w-0 flex-1 pr-2">
                        <div className="text-sm font-semibold text-white truncate">{lot.parking_lot_name || lot.parking_lot?.name || "Parking Lot"}</div>
                        <div className="text-slate-400 text-xs mt-0.5">{lot.available_slots} / {lot.total_slots} slots free</div>
                      </div>
                      <div className="text-right shrink-0">
                        <div className="text-sm font-bold text-white">{rate.toFixed(0)}%</div>
                        <div className="flex items-center justify-end gap-1 mt-0.5">
                          <span className={`w-2 h-2 rounded-full ${color}`} />
                          <span className="text-[10px] text-slate-400 uppercase font-semibold">Live</span>
                        </div>
                      </div>
                    </div>
                  );
                })}
                {(!occupancyData?.lots || occupancyData.lots.length === 0) && (
                  <div className="text-slate-500 text-xs text-center py-12">No edge lots connected yet</div>
                )}
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
