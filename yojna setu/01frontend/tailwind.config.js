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
          blue: "#0a2540",
          navy: "#0d365e",
          sky: "#0070f3",
          lightsky: "#e6f0ff",
          saffron: "#ff6b00",
          saffronlight: "#fff2e8",
          emerald: "#059669",
          emeraldlight: "#ecfdf5",
          amber: "#d97706",
          amberlight: "#fffbe6",
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
        'glow-saffron': '0 0 25px -5px rgba(255, 107, 0, 0.3)',
        'glow-sky': '0 0 25px -5px rgba(0, 112, 243, 0.3)',
        'glow-emerald': '0 0 25px -5px rgba(5, 150, 105, 0.3)',
        'card-hover': '0 20px 35px -10px rgba(15, 23, 42, 0.08), 0 0 1px 1px rgba(15, 23, 42, 0.05)',
      }
    },
  },
  plugins: [],
}
