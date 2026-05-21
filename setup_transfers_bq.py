#!/usr/bin/env python3
import os
import subprocess
import glob
import json
import sys
from config_loader import get_config

def create_transfer(project_id, transfer_location, dataset, base_name, s3_bucket, 
                 access_key_id, secret_access_key, file_format="CSV", 
                 field_delimiter=";", skip_leading_rows="1", 
                 write_disposition="WRITE_TRUNCATE", test_suffix=True):
    """
    Create a single BigQuery transfer configuration for an S3 CSV file.
    
    Args:
        project_id (str): Google Cloud project ID
        transfer_location (str): Location for the transfer (e.g., 'eu', 'us')
        dataset (str): BigQuery dataset name
        base_name (str): Base table name (without _test suffix)
        s3_bucket (str): S3 bucket name (without s3:// prefix)
        access_key_id (str): AWS access key ID
        secret_access_key (str): AWS secret access key
        file_format (str): File format (default: CSV)
        field_delimiter (str): Field delimiter (default: ;)
        skip_leading_rows (str): Number of rows to skip (default: 1)
        write_disposition (str): Write disposition (default: WRITE_TRUNCATE)
        test_suffix (bool): Whether to add _test suffix to table names
    
    Returns:
        bool: True if successful, False otherwise
    """
    # Add _test suffix if requested
    table_name = f"{base_name}_test" if test_suffix else base_name
    
    print(f"\n🔍 Processing transfer: {table_name}")
    
    try:
        # Check if the transfer exists
        check_cmd = [
            "bq", "--project_id", project_id, 
            "ls", "--transfer_config", 
            f"--transfer_location={transfer_location}"
        ]
        result = subprocess.run(check_cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        
        # More precise check for transfer existence using exact match
        # This prevents partial matches (e.g., 'user' matching 'user_profile')
        transfer_exists = False
        for line in result.stdout.splitlines():
            if line.strip() == table_name or f"|{table_name}|" in line or f"{table_name} " in line:
                transfer_exists = True
                break
                
        if transfer_exists:
            print("⏭️  Transfer exists — skipping")
            return True
        else:
            print("✅ Transfer does not exist — will create new")
        
        # Create params JSON with proper variable interpolation
        params = {
            "destination_table_name_template": base_name,
            "data_path": f"s3://{s3_bucket}/{base_name}.csv",
            "access_key_id": access_key_id,
            "secret_access_key": secret_access_key,
            "file_format": file_format,
            "field_delimiter": field_delimiter,
            "skip_leading_rows": skip_leading_rows,
            "write_disposition": write_disposition
        }
        
        # Create the transfer configuration
        create_cmd = [
            "bq", "mk", "--transfer_config",
            f"--project_id={project_id}",
            "--data_source=amazon_s3",
            f"--target_dataset={dataset}",
            f"--display_name={table_name}",
            f"--params={json.dumps(params)}",
            "--schedule=every 24 hours"
        ]
        
        subprocess.run(create_cmd, check=True)
        print(f"✅ Done with {table_name}")
        print("---------------------------------------------")
        return True
        
    except subprocess.CalledProcessError as e:
        print(f"❌ Error processing {table_name}: {str(e)}")
        return False

def setup_transfers(project_id=None, transfer_location=None,
                   dataset=None, schema_dir=None,
                   s3_bucket=None,
                   access_key_id=None,
                   secret_access_key=None,
                   file_format=None, field_delimiter=None,
                   skip_leading_rows=None, write_disposition=None,
                   test_suffix=None, table_filter=None):
    """
    Set up BigQuery transfer configurations for S3 CSV files.
    
    Args:
        project_id (str): Google Cloud project ID
        transfer_location (str): Location for the transfer (e.g., 'eu', 'us')
        dataset (str): BigQuery dataset name
        schema_dir (str): Directory containing schema JSON files
        s3_bucket (str): S3 bucket name (without s3:// prefix)
        access_key_id (str): AWS access key ID
        secret_access_key (str): AWS secret access key
        file_format (str): File format (default: CSV)
        field_delimiter (str): Field delimiter (default: ;)
        skip_leading_rows (str): Number of rows to skip (default: 1)
        write_disposition (str): Write disposition (default: WRITE_TRUNCATE)
        test_suffix (bool): Whether to add _test suffix to table names
        table_filter (list): Optional list of table names to process. If None, all tables are processed.

    Returns:
        bool: True if all transfers were processed successfully, False otherwise
    """
    # Load config and set defaults
    config = get_config()
    if not project_id:
        project_id = config.get_gcp_project_id()
    if not transfer_location:
        transfer_location = config.get_transfer_location()
    if not dataset:
        dataset = config.get_bq_dataset()
    if not schema_dir:
        schema_dir = config.get_schemas_dir()
    if not s3_bucket:
        s3_bucket = config.get_s3_bucket()
    if not access_key_id or not secret_access_key:
        access_key_id, secret_access_key = config.get_aws_credentials()
    if not file_format:
        file_format = config.get_csv_format()
    if not field_delimiter:
        field_delimiter = config.get_csv_delimiter()
    if not skip_leading_rows:
        skip_leading_rows = config.get_skip_leading_rows()
    if not write_disposition:
        write_disposition = config.get_write_disposition()
    if test_suffix is None:
        test_suffix = config.get_add_test_suffix()
    
    print("\nSetting up BigQuery Transfers")
    print("----------------------------")
    print(f"Project ID: {project_id}")
    print(f"Transfer Location: {transfer_location}")
    print(f"Dataset: {dataset}")
    print(f"Schema Directory: {schema_dir}")
    print(f"S3 Bucket: {s3_bucket}")
    print(f"AWS Access Key ID: {access_key_id[:4]}...{access_key_id[-4:]}")
    print(f"AWS Secret Access Key: {secret_access_key[:4]}...{secret_access_key[-4:]}")
    print(f"File Format: {file_format}")
    print(f"Field Delimiter: {field_delimiter}")
    print(f"Skip Leading Rows: {skip_leading_rows}")
    print(f"Write Disposition: {write_disposition}")
    print(f"Test Suffix: {'Enabled' if test_suffix else 'Disabled'}")
    
    
    # Set environment variables for authentication
    os.environ["CLOUDSDK_AUTH_BROWSER"] = "never"
    
    # Check if schema directory exists
    if not os.path.isdir(schema_dir):
        print(f"Error: Schema directory '{schema_dir}' does not exist!")
        return False
    
    # Get all schema files
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

    total_files = len(schema_files)
    if table_filter:
        print(f"Filtering to {total_files} table(s): {', '.join(table_filter)}")
    else:
        print(f"Found {total_files} schema files to process")
    
    print("⚠️ NOTE: You may need to authenticate for each transfer.")
    print("This process may require multiple authentication steps.")
    input("Press Enter to continue...")
    
    success_count = 0
    error_count = 0
    
    print("---------------------------------------------")
    
    # Process each schema file individually
    for i, schema_file in enumerate(schema_files):
        base_table_name = os.path.basename(schema_file).replace(".json", "")
        
        # Print progress information
        print(f"\n⌛ File {i + 1} of {total_files}")
        
        # Create transfer for this table
        if create_transfer(project_id, transfer_location, dataset, base_table_name, s3_bucket,
                          access_key_id, secret_access_key, file_format, field_delimiter,
                          skip_leading_rows, write_disposition, test_suffix):
            success_count += 1
        else:
            error_count += 1
    
    print("\n---------------------------------------------")
    print(f"\n🏁 Transfer processing complete: {success_count} successful, {error_count} errors 🏁")
    
    return error_count == 0

def main():
    """Command line interface for setting up BigQuery transfers."""
    # Load config for defaults
    config = get_config()
    project_id = config.get_gcp_project_id()
    transfer_location = config.get_transfer_location()
    dataset = config.get_bq_dataset()
    schema_dir = config.get_schemas_dir()
    s3_bucket = config.get_s3_bucket()
    access_key_id, secret_access_key = config.get_aws_credentials()
    file_format = config.get_csv_format()
    field_delimiter = config.get_csv_delimiter()
    skip_leading_rows = config.get_skip_leading_rows()
    write_disposition = config.get_write_disposition()
    test_suffix = config.get_add_test_suffix()
    
    # Allow command line arguments to override defaults
    if len(sys.argv) > 1:
        project_id = sys.argv[1]
    if len(sys.argv) > 2:
        dataset = sys.argv[2]
    if len(sys.argv) > 3:
        schema_dir = sys.argv[3]
    if len(sys.argv) > 4:
        s3_bucket = sys.argv[4]
    if len(sys.argv) > 5:
        access_key_id = sys.argv[5]
    if len(sys.argv) > 6:
        secret_access_key = sys.argv[6]
    if len(sys.argv) > 7:
        file_format = sys.argv[7]
    if len(sys.argv) > 8:
        field_delimiter = sys.argv[8]
    if len(sys.argv) > 9:
        skip_leading_rows = sys.argv[9]
    if len(sys.argv) > 10:
        write_disposition = sys.argv[10]
    if len(sys.argv) > 11:
        test_suffix = sys.argv[11].lower() in ("true", "yes", "1")
    
    return setup_transfers(
        project_id, transfer_location, dataset, schema_dir, s3_bucket,
        access_key_id, secret_access_key, file_format, field_delimiter,
        skip_leading_rows, write_disposition, test_suffix
    )

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
