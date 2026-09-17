import { defineConfig } from 'vitest/config'
import react from '@vitejs/plugin-react'
import tailwindcss from '@tailwindcss/vite'

export default defineConfig({
  plugins: [react(), tailwindcss()],
  server: {
    port: 5173,
    host: '0.0.0.0',
    proxy: {
      '/api': {
        target: 'http://server:8000',
        changeOrigin: true,
      },
    },
    watch: {
      usePolling: true,
    },
  },
  build: {
    chunkSizeWarningLimit: 600,
    rollupOptions: {
      output: {
        manualChunks(id) {
          if (id.includes('node_modules')) {
            // Core React ecosystem runtime
            if (id.includes('react-router-dom') || id.includes('react-dom') || id.includes('react/')) {
              return 'vendor-react';
            }
            // Map engines (only loaded on Demand)
            if (id.includes('leaflet') || id.includes('react-leaflet')) {
              return 'vendor-maps';
            }
            // Lucide Iconography
            if (id.includes('lucide-react')) {
              return 'vendor-icons';
            }
          }
        },
      },
    },
  },
  test: {
    environment: 'jsdom',
    globals: true,
    setupFiles: './src/setupTests.ts',
  },
})
