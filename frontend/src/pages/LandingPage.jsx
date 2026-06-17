import { Link } from "react-router-dom";
import { motion } from "framer-motion";
import {
  RiMapPinLine, RiBrainLine, RiShieldCheckLine,
  RiMoneyDollarCircleLine, RiCameraLine, RiBarChartBoxLine,
  RiArrowRightLine, RiParkingBoxLine,
} from "react-icons/ri";

const features = [
  {
    icon: <RiBrainLine size={26} />,
    title: "AI-Powered Recommendations",
    desc: "KNN + XGBoost ensemble ranks parking options by compatibility, distance, price, and real demand.",
    color: "from-primary-500 to-primary-700",
  },
  {
    icon: <RiCameraLine size={26} />,
    title: "Real-Time Occupancy Detection",
    desc: "YOLOv8 + OpenCV monitors every slot from CCTV feeds — you only see genuinely available spaces.",
    color: "from-accent-500 to-accent-700",
  },
  {
    icon: <RiMapPinLine size={26} />,
    title: "Live Demand Heatmaps",
    desc: "Google Maps overlays show parking hotspots so you can decide before you drive.",
    color: "from-emerald-500 to-emerald-700",
  },
  {
    icon: <RiMoneyDollarCircleLine size={26} />,
    title: "Dynamic Billing & Refunds",
    desc: "Pay only for actual time used. Unused duration is automatically refunded via Razorpay.",
    color: "from-amber-500 to-amber-700",
  },
  {
    icon: <RiBarChartBoxLine size={26} />,
    title: "Owner Analytics Dashboard",
    desc: "Track earnings, occupancy trends, 24-hour demand forecasts, and review scores.",
    color: "from-rose-500 to-rose-700",
  },
  {
    icon: <RiShieldCheckLine size={26} />,
    title: "Fraud Detection",
    desc: "Isolation Forest anomaly detection flags suspicious booking patterns before they cause damage.",
    color: "from-cyan-500 to-cyan-700",
  },
];

const stats = [
  { value: "10K+", label: "Parking Spaces" },
  { value: "98%",  label: "Detection Accuracy" },
  { value: "₹0",   label: "Extra Charges" },
  { value: "24/7", label: "AI Monitoring" },
];

const fadeUp = {
  hidden: { opacity: 0, y: 30 },
  show: (i) => ({ opacity: 1, y: 0, transition: { delay: i * 0.1, duration: 0.5 } }),
};

export default function LandingPage() {
  return (
    <div className="overflow-hidden">

      {/* ── Hero ──────────────────────────────────────────────────────────── */}
      <section className="relative min-h-[92vh] flex items-center justify-center px-4 py-20">
        {/* ambient blobs */}
        <div className="absolute inset-0 overflow-hidden pointer-events-none">
          <div className="absolute -top-40 left-1/2 -translate-x-1/2 w-[700px] h-[700px]
                          rounded-full bg-primary-600/10 blur-[120px]" />
          <div className="absolute top-1/3 right-0 w-[400px] h-[400px]
                          rounded-full bg-accent-600/8 blur-[100px]" />
          {/* grid pattern */}
          <div className="absolute inset-0 opacity-[0.03]"
               style={{ backgroundImage: "radial-gradient(circle, #fff 1px, transparent 1px)", backgroundSize: "32px 32px" }} />
        </div>

        <div className="relative z-10 max-w-5xl mx-auto text-center">
          <motion.div
            initial={{ opacity: 0, scale: 0.9 }}
            animate={{ opacity: 1, scale: 1 }}
            transition={{ duration: 0.5 }}
            className="inline-flex items-center gap-2 px-4 py-2 rounded-full
                       border border-primary-500/30 bg-primary-500/10
                       text-primary-300 text-sm font-medium mb-8"
          >
            <span className="w-2 h-2 rounded-full bg-primary-400 animate-pulse" />
            AI-Powered Smart Parking Marketplace
          </motion.div>

          <motion.h1
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.6, delay: 0.1 }}
            className="font-display font-extrabold text-5xl md:text-7xl leading-tight mb-6"
          >
            Park Smarter with{" "}
            <span className="text-gradient glow-text">AI Intelligence</span>
          </motion.h1>

          <motion.p
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.6, delay: 0.2 }}
            className="text-slate-400 text-lg md:text-xl max-w-2xl mx-auto mb-10 leading-relaxed"
          >
            SmartPark AI connects drivers with private parking owners using real-time
            computer vision, ML recommendations, and dynamic pricing — so you always
            find the <span className="text-white font-medium">perfect spot</span>.
          </motion.p>

          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.6, delay: 0.3 }}
            className="flex flex-col sm:flex-row items-center justify-center gap-4"
          >
            <Link to="/register" className="btn-primary text-base px-8 py-4 shadow-glow-md">
              Start Parking Free <RiArrowRightLine />
            </Link>
            <Link to="/search" className="btn-secondary text-base px-8 py-4">
              <RiMapPinLine /> Find Parking Now
            </Link>
          </motion.div>

          {/* Stats strip */}
          <motion.div
            initial={{ opacity: 0, y: 30 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.5, duration: 0.6 }}
            className="mt-16 grid grid-cols-2 md:grid-cols-4 gap-4 max-w-2xl mx-auto"
          >
            {stats.map((s) => (
              <div key={s.label} className="glass-card px-4 py-5 text-center">
                <div className="font-display font-bold text-3xl text-gradient">{s.value}</div>
                <div className="text-slate-400 text-xs mt-1">{s.label}</div>
              </div>
            ))}
          </motion.div>
        </div>
      </section>

      {/* ── How It Works ──────────────────────────────────────────────────── */}
      <section className="py-24 px-4 max-w-6xl mx-auto">
        <div className="text-center mb-16">
          <h2 className="section-title text-4xl">How SmartPark AI Works</h2>
          <p className="section-subtitle text-base mt-3 max-w-xl mx-auto">
            Three simple steps powered by computer vision and machine learning
          </p>
        </div>
        <div className="grid md:grid-cols-3 gap-6">
          {[
            { step: "01", title: "Search Your Destination", desc: "Enter your vehicle type, destination, and how long you'll park. Our AI fetches real-time availability." },
            { step: "02", title: "AI Recommends Best Spots", desc: "XGBoost + KNN rank lots by distance, price, compatibility, demand, and YOLOv8-verified occupancy." },
            { step: "03", title: "Book, Park & Auto-Pay",   desc: "Reserve with Razorpay. Drive in, drive out. Bill is calculated on actual time. Unused time auto-refunded." },
          ].map((step, i) => (
            <motion.div
              key={step.step}
              custom={i} variants={fadeUp} initial="hidden" whileInView="show" viewport={{ once: true }}
              className="glass-card-hover p-8 flex flex-col gap-4"
            >
              <div className="text-5xl font-display font-extrabold text-gradient opacity-40">{step.step}</div>
              <h3 className="font-semibold text-white text-xl">{step.title}</h3>
              <p className="text-slate-400 leading-relaxed text-sm">{step.desc}</p>
            </motion.div>
          ))}
        </div>
      </section>

      {/* ── Features ──────────────────────────────────────────────────────── */}
      <section className="py-24 px-4 bg-white/[0.02] border-y border-white/5">
        <div className="max-w-6xl mx-auto">
          <div className="text-center mb-16">
            <h2 className="section-title text-4xl">Everything You Need</h2>
            <p className="section-subtitle text-base mt-3">Built for drivers, owners, and cities</p>
          </div>
          <div className="grid sm:grid-cols-2 lg:grid-cols-3 gap-6">
            {features.map((f, i) => (
              <motion.div
                key={f.title}
                custom={i} variants={fadeUp} initial="hidden" whileInView="show" viewport={{ once: true }}
                className="glass-card-hover p-6 flex flex-col gap-4 group"
              >
                <div className={`w-12 h-12 rounded-xl bg-gradient-to-br ${f.color}
                                 flex items-center justify-center text-white
                                 shadow-lg group-hover:scale-110 transition-transform duration-300`}>
                  {f.icon}
                </div>
                <h3 className="font-semibold text-white">{f.title}</h3>
                <p className="text-slate-400 text-sm leading-relaxed">{f.desc}</p>
              </motion.div>
            ))}
          </div>
        </div>
      </section>

      {/* ── CTA ───────────────────────────────────────────────────────────── */}
      <section className="py-32 px-4 text-center">
        <motion.div
          initial={{ opacity: 0, scale: 0.95 }}
          whileInView={{ opacity: 1, scale: 1 }}
          viewport={{ once: true }}
          className="max-w-2xl mx-auto glass-card p-12 relative overflow-hidden"
        >
          <div className="absolute inset-0 bg-glow-primary pointer-events-none" />
          <RiParkingBoxLine className="text-primary-400 text-5xl mx-auto mb-6 animate-float" />
          <h2 className="font-display font-bold text-3xl text-white mb-4">
            Ready to Park Smarter?
          </h2>
          <p className="text-slate-400 mb-8">
            Join thousands of drivers and parking owners on SmartPark AI.
          </p>
          <Link to="/register" className="btn-primary text-base px-10 py-4 shadow-glow-lg">
            Get Started — It's Free <RiArrowRightLine />
          </Link>
        </motion.div>
      </section>

      {/* Footer */}
      <footer className="border-t border-white/8 py-8 text-center text-slate-500 text-sm">
        © {new Date().getFullYear()} SmartPark AI. Built with ❤️ for smart cities.
      </footer>
    </div>
  );
}
