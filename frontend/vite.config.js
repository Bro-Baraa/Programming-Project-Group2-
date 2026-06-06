import { defineConfig } from 'vite';

export default defineConfig({
  server: {
    port: 8080,
    strictPort: false,
    proxy: {
      '/api': {
        target: 'http://localhost:8001',
        changeOrigin: true,
      }
    },
    open: true
  },
  build: {
    outDir: 'dist',
    emptyOutDir: true
  }
});
