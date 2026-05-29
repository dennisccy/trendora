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
