#!/usr/bin/env python3
"""
One-click fix for broken BigQuery tables.

Usage:
    python3 fix_tables.py account_userprofile community_group
    python3 fix_tables.py community_comment community_group community_post
"""

import os
import sys
import subprocess
import tempfile

from config_loader import get_config
from create_schemas import get_bigquery_schema
from replace_schema_bq import replace_bigquery_schemas


def download_single_csv(s3_bucket, table_name, dest_dir, access_key, secret_key):
    """Download a single CSV file from S3."""
    os.makedirs(dest_dir, exist_ok=True)

    s3_uri = f"s3://{s3_bucket}/{table_name}.csv"
    local_path = os.path.join(dest_dir, f"{table_name}.csv")

    env = os.environ.copy()
    env["AWS_ACCESS_KEY_ID"] = access_key
    env["AWS_SECRET_ACCESS_KEY"] = secret_key

    print(f"⬇️  Downloading {s3_uri} ...")
    result = subprocess.run(
        ["aws", "s3", "cp", s3_uri, local_path],
        capture_output=True, text=True, env=env,
    )

    if result.returncode != 0:
        print(f"❌ Failed to download {table_name}.csv: {result.stderr.strip()}")
        return None

    print(f"✅ Downloaded {table_name}.csv")
    return local_path


def generate_single_schema(csv_path, schema_dir):
    """Generate a BigQuery schema JSON for a single CSV file."""
    import json

    os.makedirs(schema_dir, exist_ok=True)
    filename = os.path.basename(csv_path)
    table_name = os.path.splitext(filename)[0]

    schema = get_bigquery_schema(csv_path)
    schema_path = os.path.join(schema_dir, f"{table_name}.json")

    with open(schema_path, "w") as f:
        json.dump(schema, f, indent=2)

    print(f"📄 Schema generated: {schema_path}")
    return schema_path


def main():
    if len(sys.argv) < 2:
        print("Usage: python3 fix_tables.py <table_name> [table_name ...]")
        print("Example: python3 fix_tables.py account_userprofile community_group")
        sys.exit(1)

    table_names = sys.argv[1:]
    config = get_config()

    print(f"\n{'='*50}")
    print(f"Fixing {len(table_names)} table(s): {', '.join(table_names)}")
    print(f"{'='*50}")

    # Load config
    s3_bucket = config.get_s3_bucket()
    project_id = config.get_gcp_project_id()
    dataset = config.get_bq_dataset()
    access_key, secret_key = config.get_aws_credentials()

    if not access_key or not secret_key:
        print("❌ AWS credentials not found. Set them in your .env file.")
        sys.exit(1)

    # Use a temp directory for downloads, write schemas to the main schemas dir
    schema_dir = config.get_schemas_dir()

    with tempfile.TemporaryDirectory(prefix="bq_fix_") as tmp_dir:
        print(f"\n--- Step 1/3: Download CSVs from S3 ---")
        downloaded = []
        for table in table_names:
            csv_path = download_single_csv(s3_bucket, table, tmp_dir, access_key, secret_key)
            if csv_path:
                downloaded.append((table, csv_path))
            else:
                print(f"⚠️  Skipping {table} — download failed")

        if not downloaded:
            print("\n❌ No files downloaded. Nothing to do.")
            sys.exit(1)

        print(f"\n--- Step 2/3: Generate schemas ---")
        for table, csv_path in downloaded:
            generate_single_schema(csv_path, schema_dir)

    # Step 3: Replace BQ tables (only the specified ones)
    print(f"\n--- Step 3/3: Replace BigQuery tables ---")
    tables_to_fix = [table for table, _ in downloaded]
    success = replace_bigquery_schemas(project_id, dataset, schema_dir, tables_to_fix)

    print(f"\n{'='*50}")
    if success:
        print(f"✅ All done! Fixed: {', '.join(tables_to_fix)}")
        print(f"The existing transfers will load fresh data on their next scheduled run.")
    else:
        print(f"⚠️  Completed with errors. Check the output above.")
    print(f"{'='*50}")

    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
