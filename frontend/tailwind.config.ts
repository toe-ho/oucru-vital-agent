import type { Config } from "tailwindcss";

const config: Config = {
  content: ["./app/**/*.{ts,tsx}", "./components/**/*.{ts,tsx}"],
  theme: {
    extend: {
      colors: {
        brand: {
          900: "#1e3a5f",
          700: "#2563a8",
          100: "#dbeafe",
        },
      },
    },
  },
  plugins: [],
};

export default config;
