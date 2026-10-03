import type { Config } from "tailwindcss";

// Mirrors ice-ds tokens (colors / shadows / fonts). ice-ds 1.0.4 documents
// `iceTailwindTokens` but doesn't export it yet, so the values live here.
export default {
  content: ["./index.html", "./src/**/*.{ts,tsx}"],
  theme: {
    extend: {
      colors: {
        "neo-yellow": "#FFDE59",
        "neo-blue": "#5CE1E6",
        "neo-pink": "#FF66C4",
        "neo-green": "#7ED957",
        "neo-purple": "#C678DD",
        "neo-black": "#0F0F0F",
        "neo-offwhite": "#FFFDF5",
        "neo-red": "#EF4444",
        "neo-amber": "#F59E0B",
      },
      boxShadow: {
        "brutal-sm": "3px 3px 0 0 #0F0F0F",
        brutal: "4px 4px 0 0 #0F0F0F",
        "brutal-md": "6px 6px 0 0 #0F0F0F",
        "brutal-lg": "10px 10px 0 0 #0F0F0F",
      },
      fontFamily: {
        display: ['"Space Grotesk Variable"', "sans-serif"],
        sans: ['"Inter Variable"', "sans-serif"],
        mono: ['"JetBrains Mono Variable"', "monospace"],
      },
    },
  },
  plugins: [],
} satisfies Config;
