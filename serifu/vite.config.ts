import { defineConfig } from 'vitest/config';
import react from '@vitejs/plugin-react';
import { VitePWA } from 'vite-plugin-pwa';

export default defineConfig({
  plugins: [
    react(),
    VitePWA({
      registerType: 'autoUpdate',
      includeAssets: ['apple-touch-icon.png'],
      manifest: {
        name: 'Serifu 台詞 — voice your favorite scenes',
        short_name: 'Serifu',
        description:
          'Practice Japanese by voicing anime scenes with friends — synced video, furigana scripts, speech scoring, voice chat.',
        lang: 'ja',
        display: 'standalone',
        orientation: 'any',
        theme_color: '#0e1014',
        background_color: '#0e1014',
        icons: [
          { src: '/icon-192.png', sizes: '192x192', type: 'image/png' },
          { src: '/icon-512.png', sizes: '512x512', type: 'image/png' },
          { src: '/icon-512-maskable.png', sizes: '512x512', type: 'image/png', purpose: 'maskable' },
        ],
      },
      workbox: {
        // Never intercept realtime or API traffic; only the app shell is cached.
        navigateFallback: '/index.html',
        navigateFallbackDenylist: [/^[/]socket[.]io/, /^[/]api[/]/, /^[/]healthz/],
      },
    }),
  ],
  server: {
    proxy: {
      '/socket.io': {
        target: 'http://localhost:3001',
        ws: true,
      },
    },
  },
  build: {
    outDir: 'dist',
  },
  test: {
    environment: 'node',
    include: ['server/**/*.test.ts', 'client/src/**/*.test.ts'],
  },
});
