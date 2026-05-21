#!/usr/bin/env python3
import os
import subprocess
import glob
import sys
from config_loader import get_config


def replace_bigquery_schemas(
    project_id=None, dataset=None, schema_dir=None, table_filter=None
):
    """
    Replace BigQuery tables with new schemas.
    This is equivalent to the replace_schema_bq.sh script.

    Args:
        project_id (str): Google Cloud project ID
        dataset (str): BigQuery dataset name
        schema_dir (str): Directory containing schema JSON files
        table_filter (list): Optional list of table names to process. If None, all tables are processed.

    Returns:
        bool: True if successful, False otherwise
    """
    # Load config and set defaults
    config = get_config()
    if not project_id:
        project_id = config.get_gcp_project_id()
    if not dataset:
        dataset = config.get_bq_dataset()
    if not schema_dir:
        schema_dir = config.get_schemas_dir()
    
    print("\nReplacing BigQuery Schemas")
    print("-------------------------")
    print(f"Project ID: {project_id}")
    print(f"Dataset: {dataset}")
    print(f"Schema directory: {schema_dir}")

    # Check if schema directory exists
    if not os.path.isdir(schema_dir):
        print(f"Error: Schema directory '{schema_dir}' does not exist!")
        return False

    # Get all JSON schema files
    schema_files = glob.glob(os.path.join(schema_dir, "*.json"))
    if not schema_files:
        print(f"No schema files found in {schema_dir}")
        return False

    if table_filter:
        schema_files = [f for f in schema_files
                        if os.path.basename(f).replace(".json", "") in table_filter]
        if not schema_files:
            print(f"No matching schema files found for: {', '.join(table_filter)}")
            return False
        print(f"Filtering to {len(schema_files)} table(s): {', '.join(table_filter)}")
    else:
        print(f"Found {len(schema_files)} schema files to process")

    success_count = 0
    error_count = 0

    # Process each schema file
    for schema_file in schema_files:
        table_name = os.path.basename(schema_file).replace(".json", "")

        print(f"\n🔍 Processing table: {table_name}")

        try:
            # Check if the table exists
            check_cmd = [
                "bq",
                "--project_id",
                project_id,
                "show",
                f"{dataset}.{table_name}",
            ]
            result = subprocess.run(
                check_cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE
            )

            if result.returncode == 0:
                print(f"🗑️  Table exists — deleting: {dataset}.{table_name}")
                # Delete the table
                delete_cmd = [
                    "bq",
                    "--project_id",
                    project_id,
                    "rm",
                    "-f",
                    "-t",
                    f"{dataset}.{table_name}",
                ]
                subprocess.run(delete_cmd, check=True)
            else:
                print("✅ Table does not exist — will create new")

            # Create new table with schema
            print(f"📦 Creating table: {dataset}.{table_name}")
            create_cmd = [
                "bq",
                "--project_id",
                project_id,
                "mk",
                "--table",
                f"{dataset}.{table_name}",
                schema_file,
            ]
            subprocess.run(create_cmd, check=True)

            print(f"✅ Done with {table_name}")
            print("---------------------------------------------")
            success_count += 1

        except subprocess.CalledProcessError as e:
            print(f"❌ Error processing {table_name}: {str(e)}")
            error_count += 1

    # Print summary
    print(
        f"\nProcessing complete: {success_count} tables updated successfully, {error_count} errors"
    )

    return error_count == 0


def main():
    """Command line interface for replacing BigQuery schemas."""
    # Load config for defaults
    config = get_config()
    project_id = config.get_gcp_project_id()
    dataset = config.get_bq_dataset()
    schema_dir = config.get_schemas_dir()

    # Allow command line arguments to override defaults
    if len(sys.argv) > 1:
        project_id = sys.argv[1]
    if len(sys.argv) > 2:
        dataset = sys.argv[2]
    if len(sys.argv) > 3:
        schema_dir = sys.argv[3]

    return replace_bigquery_schemas(project_id, dataset, schema_dir)


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
