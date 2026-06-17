/**
 * OccupancyTrendChart — 48-point occupancy trend line chart
 * Color-coded background bands: green / yellow / red zones
 * Used in OwnerDashboard and AdminPanel
 */

import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  LineElement,
  PointElement,
  Title,
  Tooltip,
  Legend,
  Filler,
} from "chart.js";
import { Line } from "react-chartjs-2";
import { useMemo } from "react";

ChartJS.register(
  CategoryScale, LinearScale, LineElement, PointElement,
  Title, Tooltip, Legend, Filler
);

// Utility: format timestamp for chart label
const fmtTime = (ts) => {
  try {
    const d = new Date(ts);
    return `${d.getHours().toString().padStart(2, "0")}:${d.getMinutes().toString().padStart(2, "0")}`;
  } catch {
    return ts;
  }
};

const GRADIENT_COLOR = (pct) => {
  if (pct < 40)  return "rgba(34,197,94,0.7)";
  if (pct < 70)  return "rgba(245,158,11,0.7)";
  return               "rgba(239,68,68,0.7)";
};

export default function OccupancyTrendChart({ history = [], height = 120, title = "Occupancy Trend" }) {
  const labels = useMemo(
    () => history.map((h) => fmtTime(h.recorded_at)),
    [history]
  );

  const dataPoints = useMemo(
    () => history.map((h) => parseFloat((h.occupancy_rate).toFixed(1))),
    [history]
  );

  // Dynamic point colors
  const pointColors = dataPoints.map((v) => GRADIENT_COLOR(v));

  const data = {
    labels,
    datasets: [
      {
        label: "Occupancy %",
        data: dataPoints,
        borderColor: "#29a8ff",
        backgroundColor: "rgba(41,168,255,0.10)",
        borderWidth: 2,
        pointBackgroundColor: pointColors,
        pointBorderColor: pointColors,
        pointRadius: 3,
        pointHoverRadius: 5,
        tension: 0.4,
        fill: true,
      },
    ],
  };

  const options = {
    responsive: true,
    maintainAspectRatio: false,
    plugins: {
      legend: { display: false },
      tooltip: {
        mode: "index",
        intersect: false,
        callbacks: {
          label: (ctx) => ` ${ctx.parsed.y.toFixed(1)}% occupied`,
        },
      },
    },
    scales: {
      x: {
        grid: { color: "rgba(255,255,255,0.04)" },
        ticks: {
          color: "#64748b",
          font: { size: 10 },
          maxTicksLimit: 8,
        },
      },
      y: {
        min: 0,
        max: 100,
        grid: { color: "rgba(255,255,255,0.04)" },
        ticks: {
          color: "#64748b",
          font: { size: 10 },
          callback: (v) => `${v}%`,
        },
      },
    },
  };

  if (!history.length) {
    return (
      <div className="flex items-center justify-center h-24 text-slate-500 text-sm">
        No trend data yet — waiting for edge service
      </div>
    );
  }

  return (
    <div>
      {title && (
        <div className="text-xs text-slate-400 mb-2">{title}</div>
      )}
      <div style={{ height }}>
        <Line data={data} options={options} />
      </div>
      {/* Zone legend */}
      <div className="flex gap-4 mt-2 justify-center">
        {[
          { color: "bg-emerald-500", label: "Low (0–40%)" },
          { color: "bg-amber-500",   label: "Med (40–70%)" },
          { color: "bg-red-500",     label: "High (70–100%)" },
        ].map((z) => (
          <div key={z.label} className="flex items-center gap-1.5 text-xs text-slate-400">
            <div className={`w-2.5 h-2.5 rounded-full ${z.color} opacity-80`} />
            {z.label}
          </div>
        ))}
      </div>
    </div>
  );
}
