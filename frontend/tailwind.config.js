/** @type {import('tailwindcss').Config} */
export default {
  content: ['./index.html', './src/**/*.{js,ts,jsx,tsx}'],
  theme: {
    extend: {
      colors: { ink: '#12333d', teal: { 50: '#effaf8', 100: '#d7f2ed', 500: '#1f9d8b', 600: '#167f72', 700: '#12665d', 900: '#073b4c' }, coral: '#e9705e', sand: '#f7f3ea' },
      boxShadow: { soft: '0 16px 40px rgba(7,59,76,.09)' },
      fontFamily: { sans: ['Inter', 'ui-sans-serif', 'system-ui', 'sans-serif'] },
    },
  },
  plugins: [],
}

