import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react-swc'

// https://vite.dev/config/
export default defineConfig({
  plugins: [react()],
  server: {
    proxy: {
      '/admin': 'http://localhost:8000',
      '/api': 'http://localhost:8000',
      '/static': 'http://localhost:8000'
    }
  }
})
