import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';
import path from 'path';
import { fileURLToPath } from 'url';

const __dirname = path.dirname(fileURLToPath(import.meta.url));

export default defineConfig(({ mode }) => ({
  plugins: [react()],
  base: mode === 'production' ? '/map/' : '/',
  define: {
    'process.env': {},
    'process.version': JSON.stringify(''),
    'process.versions': JSON.stringify({}),
    global: 'globalThis'
  },
  server: {
    port: 5174,
    proxy: {
      '/api': {
        target: 'http://localhost:8000',
        changeOrigin: true
      }
    },
    fs: {
      // Allow serving files from node_modules
      allow: ['..']
    }
  },
  ssr: {
    noExternal: ['kepler.gl', 'react-palm']
  },
  optimizeDeps: {
    exclude: [],
    include: [
      'react',
      'react-dom',
      'react-redux',
      'redux',
      '@kepler.gl/components',
      '@kepler.gl/actions',
      '@kepler.gl/reducers',
      '@kepler.gl/processors',
      '@kepler.gl/schemas'
    ],
    esbuildOptions: {
      target: 'es2020'
    }
  },
  resolve: {
    alias: {
      assert: 'assert'
    }
  },
  build: {
    // Use environment variable to determine output path
    // In Docker builds, use 'dist' directory (default for Vite)
    // In local development, output directly to backend static directory
    outDir: process.env.DOCKER_BUILD === 'true' ? 'dist' : '../../src/pypsa_app/backend/static/map',
    emptyOutDir: true,
    commonjsOptions: {
      include: [/node_modules/],
      transformMixedEsModules: true
    }
  }
}));
