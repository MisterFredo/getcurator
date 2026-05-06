/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
    "./app/**/*.{js,ts,jsx,tsx}",
    "./components/**/*.{js,ts,jsx,tsx}",
    "./contexts/**/*.{js,ts,jsx,tsx}",
    "./lib/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        ratecard: {
          green: "#99C221",
          blue: "#10323d",
          gray: "#2C2C2C",
          light: "#F7F9FA",
          border: "#E5E7EB",
        },
      },
      boxShadow: {
        card: "0 1px 2px rgba(0,0,0,0.04)",
        cardHover: "0 4px 12px rgba(0,0,0,0.08)",
      },
      borderRadius: {
        xl: "0.75rem",
        "2xl": "1rem",
      },
    },
  },
  plugins: [
    require("@tailwindcss/typography"),
  ],
};
