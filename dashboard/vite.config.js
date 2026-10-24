import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

// Backend used by `npm run dev`; override with WAVEDISP_BACKEND=http://pi:5000
const backend = process.env.WAVEDISP_BACKEND || "http://127.0.0.1:5000";

// https://vite.dev/config/
export default defineConfig({
  plugins: [react()],
  server: {
    proxy: {
      "/api": {
        target: backend,
        changeOrigin: true,
        secure: false,
        configure: (proxy) => {
          // The backend rejects cross-origin writes; through the dev proxy the
          // browser's Origin (localhost:5173) would not match the backend host.
          proxy.on("proxyReq", (proxyReq) => proxyReq.removeHeader("origin"));
        },
      },
    },
  },
});
