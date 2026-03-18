import { defineConfig } from 'vite';

export default defineConfig({
  // 移除 esbuild 配置，使用默认的 Babel 转换
  // esbuild: {
  //   jsx: 'automatic',
  //   jsxImportSource: 'preact',
  // },
  resolve: {
    alias: {
      react: 'preact/compat',
      'react-dom': 'preact/compat',
    },
  },
  resolve: {
    alias: {
      react: 'preact/compat',
      'react-dom': 'preact/compat',
    },
  },
  server: {
    port: 3000,
    proxy: {
      '/api': 'http://localhost:8000',
      '/ws': {
        target: 'ws://localhost:8000',
        ws: true
      }
    }
  }
});
