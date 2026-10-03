import react from '@vitejs/plugin-react'
import tailwindcss from '@tailwindcss/vite'
import { defineConfig } from 'vite'

export default defineConfig({
    plugins: [react(), tailwindcss()],
    server: {
        proxy: {
            '/api': {
                target: process.env.VITE_BACKEND_URL || 'http://127.0.0.1:5000',
                changeOrigin: true,
            },
        },
    },
})