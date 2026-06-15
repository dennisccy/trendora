import type { Config } from "tailwindcss";

/**
 * Dense, dark analytical workstation palette (project-template DESIGN SYSTEM).
 * Colors map to CSS variables defined in app/globals.css so shadcn/ui primitives and
 * bespoke components share one source of truth. NO arbitrary hex/px/font sizes in components.
 */
const config: Config = {
  darkMode: ["class"],
  content: [
    "./app/**/*.{ts,tsx}",
    "./components/**/*.{ts,tsx}",
    "./lib/**/*.{ts,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        bg: "var(--bg)",
        surface: { DEFAULT: "var(--surface)", 2: "var(--surface-2)" },
        border: { DEFAULT: "var(--border)", strong: "var(--border-strong)" },
        accent: "var(--accent)",
        pos: "var(--pos)",
        neg: "var(--neg)",
        warn: "var(--warn)",
        text: { DEFAULT: "var(--text)", muted: "var(--text-muted)", faint: "var(--text-faint)" },
        // J-74 availability-heatmap density scale (six perceptually-ordered multi-hue buckets) +
        // the per-bucket day-number text-contrast tokens. One source: globals.css CSS vars (no cell hex).
        heat: {
          0: "var(--heat-0)",
          1: "var(--heat-1)",
          2: "var(--heat-2)",
          3: "var(--heat-3)",
          4: "var(--heat-4)",
          5: "var(--heat-5)",
        },
        "heat-text": {
          0: "var(--heat-text-0)",
          1: "var(--heat-text-1)",
          2: "var(--heat-text-2)",
          3: "var(--heat-text-3)",
          4: "var(--heat-text-4)",
          5: "var(--heat-text-5)",
        },
        // shadcn/ui semantic aliases (so generated primitives theme correctly)
        background: "var(--bg)",
        foreground: "var(--text)",
        card: "var(--surface)",
        "card-foreground": "var(--text)",
        muted: { DEFAULT: "var(--surface-2)", foreground: "var(--text-muted)" },
        primary: { DEFAULT: "var(--accent)", foreground: "var(--bg)" },
        ring: "var(--accent)",
      },
      fontFamily: {
        sans: ["var(--font-sans)", "system-ui", "sans-serif"],
        mono: ["var(--font-mono)", "ui-monospace", "SFMono-Regular", "Menlo", "monospace"],
      },
      borderRadius: {
        lg: "0.5rem",
        md: "0.375rem",
        sm: "0.25rem",
      },
    },
  },
  plugins: [require("tailwindcss-animate")],
};

export default config;
