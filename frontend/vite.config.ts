import { defineConfig, loadEnv } from 'vite';
import react from '@vitejs/plugin-react';
import tailwindcss from '@tailwindcss/vite';
export default defineConfig(({ mode }) => {
    const env = loadEnv(mode, '.', '');
    if (env.VERCEL === '1' && !/^https:\/\/[^/\s]+/.test(env.VITE_API_URL || '')) {
        throw new Error('Defina VITE_API_URL com a URL HTTPS da API no Render antes do build da Vercel.');
    }
    return { plugins: [react(), tailwindcss()], server: { proxy: {
        '/api': { target: 'http://127.0.0.1:8000', rewrite: path => path.replace(/^\/api/, '') },
    } } };
});
