#!/usr/bin/env python3
"""Local development only: create the MinIO bucket and let anyone read the public/ folder.

Cloudflare R2 does not use bucket policies: there the bucket's public access is switched on in the
Cloudflare dashboard (custom domain), so this script refuses to run against anything but localhost.

    python scripts/init_storage.py
"""

import json
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).parent.parent))

from botocore.exceptions import ClientError

from app.core.config import settings
from app.core.storage import PUBLIC_PREFIX, S3Storage


def main() -> None:
    if "localhost" not in settings.STORAGE_ENDPOINT_URL and "127.0.0.1" not in settings.STORAGE_ENDPOINT_URL:
        sys.exit("Refusing to run: STORAGE_ENDPOINT_URL is not local. Configure R2 in the Cloudflare dashboard.")
    storage = S3Storage()
    try:
        storage.client.head_bucket(Bucket=settings.STORAGE_BUCKET)
        print(f"Bucket '{settings.STORAGE_BUCKET}' already exists")
    except ClientError:
        storage.client.create_bucket(Bucket=settings.STORAGE_BUCKET)
        print(f"Created bucket '{settings.STORAGE_BUCKET}'")
    policy = {
        "Version": "2012-10-17",
        "Statement": [
            {
                "Effect": "Allow",
                "Principal": {"AWS": ["*"]},
                "Action": ["s3:GetObject"],
                "Resource": [f"arn:aws:s3:::{settings.STORAGE_BUCKET}/{PUBLIC_PREFIX}*"],
            }
        ],
    }
    storage.client.put_bucket_policy(Bucket=settings.STORAGE_BUCKET, Policy=json.dumps(policy))
    print(f"{PUBLIC_PREFIX} is publicly readable; everything else stays private")


if __name__ == "__main__":
    main()
