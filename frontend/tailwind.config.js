// tailwind.config.js
module.exports = {
  content: [
    './src/**/*.{js,jsx,ts,tsx}',  // Asegúrate de que Tailwind observa todos los archivos JSX/TSX
    './public/index.html',  // Si estás utilizando clases en el archivo index.html de React
  ],
  theme: {
    extend: {},
  },
  plugins: [],
}
