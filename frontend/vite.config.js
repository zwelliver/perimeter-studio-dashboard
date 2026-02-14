import { defineConfig, loadEnv } from 'vite'
import react from '@vitejs/plugin-react'

// https://vitejs.dev/config/
export default defineConfig(({ mode }) => {
  // Load env variables for the current mode (development, production)
  const env = loadEnv(mode, process.cwd(), '')

  // API target: use VITE_API_URL env var if set, otherwise fall back to local FastAPI
  const apiTarget = env.VITE_API_URL || 'http://localhost:5001'

  return {
    plugins: [react()],

    // Base path: must be '/' so FastAPI can serve the app at the root URL
    base: '/',

    server: {
      host: '0.0.0.0', // Allow access from network (required for Docker/Railway dev)
      port: 3000,
      proxy: {
        // Proxy all /api/* requests to the FastAPI backend during development
        '/api': {
          target: apiTarget,
          changeOrigin: true,
          // Do NOT rewrite the path — FastAPI expects /api/* as-is
        }
      }
    },

    build: {
      // Explicitly target the dist/ directory (Railway and FastAPI static serving expect this)
      outDir: 'dist',

      // Clean the output directory before each build
      emptyOutDir: true,

      // Produce source maps for production error tracing (set to false to reduce bundle size if preferred)
      sourcemap: false,

      // Raise the chunk size warning threshold slightly; individual vendor chunks stay well below this
      chunkSizeWarningLimit: 600,

      rollupOptions: {
        output: {
          // Split heavy third-party libraries into separate cacheable chunks
          manualChunks: {
            'react-vendor': ['react', 'react-dom'],
            'chart-vendor': ['recharts'],
            'date-vendor': ['date-fns'],
            'pdf-vendor': ['jspdf', 'html2canvas'],
            'csv-vendor': ['papaparse']
          }
        }
      }
    },

    // Expose selected env variables to the client bundle under import.meta.env.*
    // Only variables prefixed with VITE_ are exposed by default — this is intentional.
    define: {
      // Make the build mode available at runtime for conditional logic if needed
      __APP_VERSION__: JSON.stringify(process.env.npm_package_version || '1.0.0')
    }
  }
})
