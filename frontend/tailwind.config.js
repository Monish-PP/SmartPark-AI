/** @type {import('tailwindcss').Config} */
export default {
  content: ["./index.html", "./src/**/*.{js,jsx,ts,tsx}"],
  darkMode: "class",
  theme: {
    extend: {
      colors: {
        primary: {
          50:  "#eef9ff",
          100: "#d8f1ff",
          200: "#b9e8ff",
          300: "#89daff",
          400: "#52c4ff",
          500: "#29a8ff",
          600: "#118af5",
          700: "#0a72e1",
          800: "#0f5cb6",
          900: "#134f8f",
          950: "#0e3160",
        },
        surface: {
          50:  "#f8fafc",
          100: "#f1f5f9",
          800: "#1e293b",
          900: "#0f172a",
          950: "#020617",
        },
        accent: {
          400: "#a78bfa",
          500: "#8b5cf6",
          600: "#7c3aed",
        },
        success: "#22c55e",
        warning: "#f59e0b",
        danger:  "#ef4444",
      },
      fontFamily: {
        sans: ["Inter", "system-ui", "sans-serif"],
        display: ["Plus Jakarta Sans", "Inter", "sans-serif"],
      },
      backgroundImage: {
        "hero-gradient": "linear-gradient(135deg, #0e3160 0%, #134f8f 40%, #0a72e1 100%)",
        "card-gradient": "linear-gradient(145deg, rgba(255,255,255,0.05) 0%, rgba(255,255,255,0.02) 100%)",
        "glow-primary": "radial-gradient(circle at 50% 0%, rgba(41,168,255,0.15) 0%, transparent 70%)",
      },
      boxShadow: {
        "glow-sm":  "0 0 12px rgba(41,168,255,0.25)",
        "glow-md":  "0 0 24px rgba(41,168,255,0.30)",
        "glow-lg":  "0 0 48px rgba(41,168,255,0.35)",
        "glass":    "0 8px 32px rgba(0,0,0,0.3), inset 0 1px 0 rgba(255,255,255,0.1)",
      },
      animation: {
        "fade-in":    "fadeIn 0.4s ease-out",
        "slide-up":   "slideUp 0.5s ease-out",
        "pulse-glow": "pulseGlow 2s ease-in-out infinite",
        "float":      "float 3s ease-in-out infinite",
      },
      keyframes: {
        fadeIn:    { from: { opacity: 0 }, to: { opacity: 1 } },
        slideUp:   { from: { opacity: 0, transform: "translateY(20px)" }, to: { opacity: 1, transform: "translateY(0)" } },
        pulseGlow: { "0%,100%": { boxShadow: "0 0 12px rgba(41,168,255,0.2)" }, "50%": { boxShadow: "0 0 32px rgba(41,168,255,0.5)" } },
        float:     { "0%,100%": { transform: "translateY(0)" }, "50%": { transform: "translateY(-8px)" } },
      },
      backdropBlur: { xs: "2px" },
    },
  },
  plugins: [],
};
