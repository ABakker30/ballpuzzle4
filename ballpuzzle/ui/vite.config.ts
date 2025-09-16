import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";
import { readFileSync } from "fs";
import { join } from "path";

// https://vitejs.dev/config/
export default defineConfig({
  plugins: [react()],
  server: { 
    port: 5173,
    // Configure middleware to serve status.json from parent directory
    middlewares: [
      {
        name: 'status-file-middleware',
        configureServer(server) {
          server.middlewares.use('/.status/status.json', (req, res, next) => {
            try {
              const statusPath = join(__dirname, '../.status/status.json');
              const statusContent = readFileSync(statusPath, 'utf-8');
              res.setHeader('Content-Type', 'application/json');
              res.setHeader('Cache-Control', 'no-cache');
              res.end(statusContent);
            } catch (error) {
              res.statusCode = 404;
              res.end('Status file not found');
            }
          });
        }
      }
    ]
  },
});
