import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'
import path from 'path'

export default defineConfig({
  plugins: [vue()],
  resolve: {
    alias: {
      '@': path.resolve(__dirname, './src')
    }
  },
  server: {
    host: '0.0.0.0',
    port: 5173,
    // 代理配置：仅 localhost 访问时生效，外网访问时直接请求
    proxy: {
      '/api': {
        target: 'http://localhost:8000',
        changeOrigin: true,
        bypass(req) {
          // 如果是外网访问，跳过代理，直接请求
          const host = req.headers.host || ''
          if (!host.includes('localhost') && !host.includes('127.0.0.1')) {
            return false
          }
        }
      }
    }
  },
  css: {
    devSourcemap: true
  }
})
