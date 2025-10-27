/** @type {import('next').NextConfig} */
const nextConfig = {
  reactStrictMode: true,
  images: {
    remotePatterns: [
      {
        protocol: 'http',
        hostname: 'localhost',
        port: '8000',
        pathname: '/api/v1/files/**',
      },
      {
        protocol: 'https',
        hostname: '**',
        pathname: '/api/v1/files/**',
      },
    ],
  },
  async rewrites() {
    // 从环境变量获取 API 基础 URL
    const apiBaseUrl = process.env.NEXT_PUBLIC_API_BASE_URL || 'http://localhost:8000/api/v1';
    
    return [
      {
        source: '/api/v1/:path*',
        destination: `${apiBaseUrl.replace('/api/v1', '')}/api/v1/:path*`,
      },
    ]
  },
  // 输出配置 - 支持独立部署
  output: 'standalone',
}

module.exports = nextConfig
