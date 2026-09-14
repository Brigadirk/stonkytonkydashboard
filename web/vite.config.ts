import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';
const allowedHosts=(process.env.FORWARD_ALLOWED_HOSTS||'').split(',').map(host=>host.trim()).filter(Boolean);
export default defineConfig({
  plugins: [react()],
  server: {allowedHosts: allowedHosts},
  preview: {allowedHosts: allowedHosts},
  build: {chunkSizeWarningLimit: 1400},
});
