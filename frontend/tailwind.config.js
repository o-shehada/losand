export default {
  content: ["./index.html", "./src/**/*.{vue,js}"],
  theme: {
    extend: {
      fontFamily: {
        sans: ["Cairo", "Inter", "ui-sans-serif", "system-ui", "sans-serif"],
        cairo: ["Cairo", "sans-serif"],
      },
      colors: {
        // Food Logger design system (matches docs/Manufacture mockups)
        primary: "#E8490F",
        "primary-light": "#FFF0EB",
        "primary-dark": "#C73D0C",
        warm: "#FAFAFA",
        surface: "#FFFFFF",
        border: "#E8E0DB",
        text: "#1A1A1A",
        muted: "#6B6B6B",
        success: "#16A34A",
        warning: "#D97706",
        danger: "#DC2626",
        manufacture: {
          ink: "#182230",
          muted: "#667085",
          line: "#E4E7EC",
          warm: "#F8FAFC",
          green: "#0F9F6E",
          greenDark: "#087452",
          amber: "#D97706",
          red: "#DC2626",
        },
        // Restaurant POS design system (matches docs/POS mockups) — namespaced
        // so it never collides with the manufacture (orange) tokens above.
        pos: {
          canvas: "#f7fbf0",
          sidebar: "#d4e8b0",
          brand: "#8cc63f",
          "brand-dark": "#6fa832",
          "brand-light": "#e8f5d0",
          danger: "#e84c3d",
          "danger-light": "#fde8e6",
          orange: "#E8490F",
          "orange-light": "#fef0eb",
          green: "#3DAA6F",
          "green-light": "#e8f5ef",
          amber: "#F5A623",
          "amber-light": "#fef8ec",
          muted: "#8a9a7a",
          surface: "#ffffff",
          border: "#ddeec8",
        },
      },
      borderRadius: {
        xl2: "16px",
      },
    },
  },
  plugins: [],
}
