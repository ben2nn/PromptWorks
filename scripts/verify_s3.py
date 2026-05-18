"""验证 MinIO/S3 存储连接"""

import boto3
from botocore.config import Config as BotoConfig

# 从 .env 读取配置
import os
from pathlib import Path

env_path = Path(__file__).parent.parent / ".env"
config = {}
if env_path.exists():
    for line in env_path.read_text().splitlines():
        line = line.strip()
        if line and not line.startswith("#") and "=" in line:
            key, value = line.split("=", 1)
            config[key.strip()] = value.strip()

endpoint_url = config.get("AWS_S3_ENDPOINT_URL")
bucket = config.get("AWS_S3_BUCKET")
region = config.get("AWS_S3_REGION", "us-east-1")
access_key = config.get("AWS_ACCESS_KEY_ID")
secret_key = config.get("AWS_SECRET_ACCESS_KEY")

print(f"Endpoint:  {endpoint_url}")
print(f"Bucket:    {bucket}")
print(f"Region:    {region}")
print(f"AccessKey: {access_key}")
print()

try:
    s3 = boto3.client(
        "s3",
        aws_access_key_id=access_key,
        aws_secret_access_key=secret_key,
        region_name=region,
        endpoint_url=endpoint_url,
        config=BotoConfig(signature_version="s3v4"),
    )

    # 测试 1: 列出桶
    print("[1/3] 列出所有桶...")
    resp = s3.list_buckets()
    buckets = [b["Name"] for b in resp["Buckets"]]
    print(f"  桶列表: {buckets}")
    if bucket in buckets:
        print(f"  ✓ 桶 '{bucket}' 存在")
    else:
        print(f"  ✗ 桶 '{bucket}' 不存在!")
        exit(1)

    # 测试 2: 列出桶内对象
    print(f"\n[2/3] 列出桶 '{bucket}' 内的对象 (前10个)...")
    resp = s3.list_objects_v2(Bucket=bucket, MaxKeys=10)
    objects = resp.get("Contents", [])
    if objects:
        for obj in objects:
            print(f"  {obj['Key']}  ({obj['Size']} bytes)")
    else:
        print("  (桶为空)")

    # 测试 3: 生成预签名 URL
    print(f"\n[3/3] 测试预签名 URL 生成...")
    if objects:
        test_key = objects[0]["Key"]
        url = s3.generate_presigned_url(
            "get_object",
            Params={"Bucket": bucket, "Key": test_key},
            ExpiresIn=3600,
        )
        print(f"  对象: {test_key}")
        print(f"  预签名 URL: {url[:120]}...")
        print(f"  ✓ 预签名 URL 生成成功")
    else:
        # 上传测试文件
        test_key = "test/verify.txt"
        s3.put_object(Bucket=bucket, Key=test_key, Body=b"hello", ContentType="text/plain")
        url = s3.generate_presigned_url(
            "get_object",
            Params={"Bucket": bucket, "Key": test_key},
            ExpiresIn=3600,
        )
        print(f"  已上传测试文件: {test_key}")
        print(f"  预签名 URL: {url[:120]}...")
        s3.delete_object(Bucket=bucket, Key=test_key)
        print(f"  已清理测试文件")
        print(f"  ✓ 预签名 URL 生成成功")

    print("\n✓ S3/MinIO 连接验证全部通过!")

except Exception as e:
    print(f"\n✗ 连接失败: {e}")
    exit(1)
