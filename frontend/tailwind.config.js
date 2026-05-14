/** @type {import('tailwindcss').Config} */
export default {
  content: ['./index.html', './src/**/*.{js,jsx}'],
  theme: {
    extend: {
      fontFamily: {
        sans: ['Inter', 'system-ui', 'sans-serif'],
        display: ['Inter', 'system-ui', 'sans-serif'],
      },
      colors: {
        ink: { 950: '#0a0e17', 900: '#111827', 800: '#1e293b' },
        accent: '#38bdf8',
        void: '#000000',
        charcoal: '#11171d',
        neon: {
          magenta: '#c084fc',
          green: '#4ade80',
        },
      },
      boxShadow: {
        glow: '0 0 32px rgba(192, 132, 252, 0.25)',
      },
    },
  },
  plugins: [],
}
