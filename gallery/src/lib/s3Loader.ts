/**
 * S3/MinIO 自定义图片加载器
 * 直接返回原始 URL，不经过 Next.js Image 优化代理
 */

export interface S3LoaderProps {
  src: string;
  width: number;
  quality?: number;
}

export default function s3Loader({ src }: S3LoaderProps): string {
  return src;
}
