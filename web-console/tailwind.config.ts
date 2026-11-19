import type { Config } from "tailwindcss";

const config: Config = {
  content: ["./app/**/*.{js,ts,jsx,tsx,mdx}"],
  theme: {
    extend: {
      colors: {
        obsidian: "#090909",
        gold: "#D4AF37",
      },
    },
  },
  plugins: [],
};

export default config;
