/** @type {import('next').NextConfig} */

// 构建图片远程域名白名单
const imageRemotePatterns = [
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
];

// S3 / MinIO bucket 域名支持
const s3BucketDomain = process.env.NEXT_PUBLIC_S3_BUCKET_DOMAIN;
if (s3BucketDomain) {
  // 解析域名和端口（MinIO 地址可能带端口，如 minio.example.com:9000）
  const lastColon = s3BucketDomain.lastIndexOf(':');
  const hasPort = lastColon > 0 && !s3BucketDomain.includes('['); // 排除 IPv6
  const s3Hostname = hasPort ? s3BucketDomain.substring(0, lastColon) : s3BucketDomain;
  const s3Port = hasPort ? s3BucketDomain.substring(lastColon + 1) : undefined;

  const s3Pattern = {
    hostname: s3Hostname,
    pathname: '/**',
  };

  // MinIO 等可能同时支持 http 和 https
  imageRemotePatterns.push(
    { protocol: 'https', port: s3Port || '', ...s3Pattern },
    { protocol: 'http', port: s3Port || '', ...s3Pattern }
  );
}

// 添加 AWS S3 通配域名（如果配置了 region）
const s3Region = process.env.NEXT_PUBLIC_S3_BUCKET_REGION;
if (s3Region) {
  imageRemotePatterns.push(
    {
      protocol: 'https',
      hostname: `*.s3.${s3Region}.amazonaws.com`,
      pathname: '/**',
    },
    {
      protocol: 'https',
      hostname: `s3.${s3Region}.amazonaws.com`,
      pathname: '/**',
    }
  );
}

const nextConfig = {
  reactStrictMode: true,
  images: {
    remotePatterns: imageRemotePatterns,
    // 添加图像加载失败时的处理
    dangerouslyAllowSVG: true,
    contentDispositionType: 'attachment',
    contentSecurityPolicy: "default-src 'self'; script-src 'none'; sandbox;",
    // 设置图像加载超时
    loader: 'default',
    deviceSizes: [640, 750, 828, 1080, 1200, 1920, 2048, 3840],
    imageSizes: [16, 32, 48, 64, 96, 128, 256, 384],
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
