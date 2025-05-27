/** @type {import('tailwindcss').Config} */
export default {
  darkMode: 'class',
  content: [
    './index.html',
    './src/**/*.{ts,tsx,js,jsx}',   // ✨ 경로 지정 (경고 해결)
  ],
  theme: {
    extend: {
      colors: {
        primary:   '#00e0ff',
        secondary: '#c471ed',
        'bg-start': '#1a1a2e',
        'bg-end':   '#16213e',
      },
      fontFamily: {
        sans: ['Pretendard', 'Inter', 'system-ui', 'sans-serif'],
      },
    },
  },
  plugins: [],
};
