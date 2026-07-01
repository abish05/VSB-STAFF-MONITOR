import type { Config } from "tailwindcss";

const config: Config = {
  darkMode: "class",
  content: [
    "./pages/**/*.{js,ts,jsx,tsx,mdx}",
    "./components/**/*.{js,ts,jsx,tsx,mdx}",
    "./app/**/*.{js,ts,jsx,tsx,mdx}",
  ],
  theme: {
    extend: {
      fontFamily: {
        display: ["Sora", "sans-serif"],
        body: ["Inter", "sans-serif"],
        mono: ["JetBrains Mono", "monospace"],
      },
      colors: {
        primary: {
          DEFAULT: "#EAB308",
          50: "#FEFCE8",
          100: "#FEF9C3",
          200: "#FEF08A",
          300: "#FDE047",
          400: "#FACC15",
          500: "#EAB308",
          600: "#CA8A04",
          700: "#A16207",
          800: "#854D0E",
        },
        secondary: {
          DEFAULT: "#F59E0B",
          500: "#F59E0B",
        },
        success: "#22C55E",
        warning: "#F59E0B",
        danger: "#EF4444",
        dark: {
          bg: "#0F172A",
          card: "#1E293B",
          border: "#334155",
          text: "#E2E8F0",
          muted: "#94A3B8",
        },
        light: {
          bg: "#F8FAFC",
          card: "#FFFFFF",
          border: "#E2E8F0",
        },
      },
      backgroundImage: {
        "gradient-primary": "linear-gradient(135deg, #EAB308, #F59E0B)",
        "gradient-dark": "linear-gradient(180deg, #0F172A 0%, #1E293B 100%)",
        "glass": "rgba(255, 255, 255, 0.05)",
      },
      boxShadow: {
        glow: "0 0 20px rgba(234, 179, 8, 0.4)",
        "glow-cyan": "0 0 20px rgba(245, 158, 11, 0.3)",
        card: "0 4px 24px rgba(0, 0, 0, 0.12)",
        "card-hover": "0 8px 40px rgba(0, 0, 0, 0.20)",
      },
      borderRadius: {
        xl: "0.75rem",
        "2xl": "1rem",
        "3xl": "1.5rem",
      },
      animation: {
        "fade-in": "fadeIn 0.3s ease-out",
        "slide-up": "slideUp 0.4s ease-out",
        "pulse-glow": "pulseGlow 2s ease-in-out infinite",
        "spin-slow": "spin 3s linear infinite",
      },
      keyframes: {
        fadeIn: {
          "0%": { opacity: "0", transform: "translateY(8px)" },
          "100%": { opacity: "1", transform: "translateY(0)" },
        },
        slideUp: {
          "0%": { opacity: "0", transform: "translateY(20px)" },
          "100%": { opacity: "1", transform: "translateY(0)" },
        },
        pulseGlow: {
          "0%, 100%": { boxShadow: "0 0 10px rgba(234, 179, 8, 0.3)" },
          "50%": { boxShadow: "0 0 30px rgba(234, 179, 8, 0.6)" },
        },
      },
      backdropBlur: {
        glass: "12px",
      },
    },
  },
  plugins: [require("@tailwindcss/typography")],
};

export default config;
