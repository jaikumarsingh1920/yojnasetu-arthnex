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
        sans: ['Inter', 'system-ui', '-apple-system', 'sans-serif'],
      }
    },
  },
  plugins: [],
}
