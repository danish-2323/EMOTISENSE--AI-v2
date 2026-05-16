import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

export default defineConfig({
  plugins: [react()],
  server: {
    port: 5173,
    proxy: {
      '/session': 'https://emotisense-e6z2.onrender.com',
      '/health':  'https://emotisense-e6z2.onrender.com',
    }
  }
})
