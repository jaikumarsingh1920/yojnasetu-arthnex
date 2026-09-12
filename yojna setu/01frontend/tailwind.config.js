/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        gov: {
          blue: "#861823",
          navy: "#861823",
          sky: "#c85310",
          lightsky: "#fff0e4",
          saffron: "#c85310",
          saffronlight: "#fff0e4",
          emerald: "#059669",
          emeraldlight: "#ecfdf5",
          amber: "#d7832d",
          amberlight: "#fff6e9",
          rose: "#e11d48",
          roselight: "#ffe4e6",
          slate: "#0f172a",
        }
      },
      fontFamily: {
        sans: ['"Plus Jakarta Sans"', 'Inter', 'system-ui', '-apple-system', 'sans-serif'],
        heading: ['Outfit', '"Plus Jakarta Sans"', 'Inter', 'sans-serif'],
      },
      boxShadow: {
        'glow-saffron': '0 0 25px -5px rgba(200, 83, 16, 0.3)',
        'glow-sky': '0 0 25px -5px rgba(200, 83, 16, 0.3)',
        'glow-emerald': '0 0 25px -5px rgba(5, 150, 105, 0.3)',
        'card-hover': '0 20px 35px -10px rgba(15, 23, 42, 0.08), 0 0 1px 1px rgba(15, 23, 42, 0.05)',
      }
    },
  },
  plugins: [],
}
