import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import tailwindcss from '@tailwindcss/vite'

export default defineConfig({
  plugins: [react(), tailwindcss()],
  server: {
    proxy: {
<<<<<<< HEAD
      '/api': {
        target: 'http://127.0.0.1:8000',
        changeOrigin: true,
      },
      '/auth': {
        target: 'http://127.0.0.1:8000',
        changeOrigin: true,
=======
      '/auth': {
        target: 'http://localhost:8000',
        changeOrigin: true,
        secure: false,
>>>>>>> 513bdb13da22d46561a8eb025f27f08d0ef241f5
      },
    },
  },
})