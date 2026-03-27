import type { Config } from "tailwindcss";

const config: Config = {
  content: [
    "./app/**/*.{ts,tsx}",
    "./components/**/*.{ts,tsx}",
    "./lib/**/*.{ts,tsx}"
  ],
  theme: {
    extend: {
      colors: {
        ink: "#11243a",
        mist: "#eef5ff",
        glow: "#9fd3c7",
        coral: "#ff8b5e",
        sand: "#f6efe7"
      },
      boxShadow: {
        soft: "0 20px 60px rgba(17, 36, 58, 0.12)"
      },
      borderRadius: {
        panel: "1.5rem"
      }
    }
  },
  plugins: []
};

export default config;
