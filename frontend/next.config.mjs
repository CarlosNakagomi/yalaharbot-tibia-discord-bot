import { PHASE_DEVELOPMENT_SERVER } from 'next/constants.js';

export default function nextConfig(phase) {
  const isDevServer = phase === PHASE_DEVELOPMENT_SERVER;

  return {
    ...(!isDevServer && {
      output: 'export',
    }),
    assetPrefix: process.env.NODE_ENV === 'production' ? '/static' : undefined,
    trailingSlash: true,
    ...(isDevServer && {
      async rewrites() {
        return [
          {
            source: '/api/:path*',
            destination: 'http://127.0.0.1:8000/api/:path*/',
          },
        ];
      },
    }),
  };
}
