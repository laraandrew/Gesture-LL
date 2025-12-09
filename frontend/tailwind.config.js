/** @type {import('tailwindcss').Config} */
export default {
  content: ['./index.html', './src/**/*.{js,jsx,ts,tsx}'],
  theme: {
    extend: {
      colors: {
        christmasRed: '#b91c1c',
        christmasGreen: '#16a34a',
      },
    },
  },
  plugins: [],
}
