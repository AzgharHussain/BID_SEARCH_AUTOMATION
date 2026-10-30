import react from '@vitejs/plugin-react'
import { defineConfig } from 'vite'

const backendPort = process.env.VITE_BACKEND_PORT || process.env.BACKEND_PORT || '7035';
const backendTarget = process.env.VITE_BACKEND_URL || `http://127.0.0.1:${backendPort}`;

// https://vite.dev/config/
export default defineConfig({
  plugins: [react()],
  server: {
    host: '0.0.0.0',
    port: 5173,
    proxy: {
      '/api': {
        target: backendTarget,
        changeOrigin: true
      }
    }
  },
  preview: {
    host: '0.0.0.0',
    port: 4173,
    proxy: {
      '/api': {
        target: backendTarget,
        changeOrigin: true
      }
    }
  }
})
