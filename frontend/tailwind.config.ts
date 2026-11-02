import type { Config } from "tailwindcss";

const config: Config = {
  content: [
    "./src/pages/**/*.{js,ts,jsx,tsx,mdx}",
    "./src/components/**/*.{js,ts,jsx,tsx,mdx}",
    "./src/app/**/*.{js,ts,jsx,tsx,mdx}",
  ],
  theme: {
    extend: {
      colors: {
        ocean: {
          950: "#030d1a",
          900: "#061424",
          800: "#0a2340",
          700: "#0d3260",
          600: "#0f4080",
          500: "#1155a5",
          400: "#1a6ec2",
          300: "#3a8fd4",
          200: "#6eb8e8",
          100: "#b0d9f5",
          50:  "#e8f4fd",
        },
        wave: {
          safe:      "#10b981",
          moderate:  "#f59e0b",
          dangerous: "#ef4444",
          critical:  "#7c3aed",
        },
      },
      fontFamily: {
        sans: ["Inter", "system-ui", "sans-serif"],
        mono: ["JetBrains Mono", "monospace"],
      },
      backgroundImage: {
        "ocean-gradient": "linear-gradient(135deg, #030d1a 0%, #061424 50%, #0a2340 100%)",
        "glow-ocean": "radial-gradient(ellipse at center, rgba(26,110,194,0.15) 0%, transparent 70%)",
      },
      animation: {
        "pulse-slow": "pulse 3s cubic-bezier(0.4, 0, 0.6, 1) infinite",
        "fade-in":    "fadeIn 0.3s ease-in-out",
        "slide-up":   "slideUp 0.3s ease-out",
        "wave":       "wave 2s ease-in-out infinite",
      },
      keyframes: {
        fadeIn: {
          "0%":   { opacity: "0" },
          "100%": { opacity: "1" },
        },
        slideUp: {
          "0%":   { transform: "translateY(10px)", opacity: "0" },
          "100%": { transform: "translateY(0)",    opacity: "1" },
        },
        wave: {
          "0%, 100%": { transform: "translateY(0)" },
          "50%":      { transform: "translateY(-6px)" },
        },
      },
      boxShadow: {
        "ocean":    "0 0 30px rgba(26,110,194,0.3)",
        "glow-sm":  "0 0 10px rgba(26,110,194,0.4)",
        "glow-md":  "0 0 20px rgba(26,110,194,0.4)",
        "glow-danger": "0 0 20px rgba(239,68,68,0.4)",
      },
    },
  },
  plugins: [],
};

export default config;
