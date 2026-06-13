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
      },
    },
  },
  plugins: [],
}
