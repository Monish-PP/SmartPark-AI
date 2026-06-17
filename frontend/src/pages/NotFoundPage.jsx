import { Link } from "react-router-dom";
import { motion } from "framer-motion";

export default function NotFoundPage() {
  return (
    <div className="min-h-[80vh] flex items-center justify-center px-4 text-center">
      <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }}>
        <div className="font-display font-extrabold text-8xl text-gradient mb-4">404</div>
        <h1 className="font-display font-bold text-2xl text-white mb-2">Page Not Found</h1>
        <p className="text-slate-400 mb-8">Looks like this parking spot doesn't exist.</p>
        <Link to="/" className="btn-primary">← Back to Home</Link>
      </motion.div>
    </div>
  );
}
