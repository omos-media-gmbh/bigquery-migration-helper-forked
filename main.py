#!/usr/bin/env python3
import os
import importlib.util
from config_loader import get_config


def clear_screen():
    """Clear the terminal screen."""
    os.system("cls" if os.name == "nt" else "clear")


def print_header():
    """Print the application header."""
    clear_screen()
    print("BigQuery Migration Helper")
    print("-------------------------")
    print()


def load_module(file_path, module_name):
    """Dynamically load a Python module from file path."""
    spec = importlib.util.spec_from_file_location(module_name, file_path)
    if not spec:
        print(f"Error: Could not load {file_path}")
        return None

    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def create_schemas():
    """Run the schema creation process."""
    print_header()
    print("Create BigQuery Schemas")
    print("---------------------")

    # Get config
    config = get_config()
    
    # Ask for bucket path
    default_path = config.get_local_bucket_dir()
    bucket_path = input(f"Enter path to CSV files [default: {default_path}]: ").strip()
    if not bucket_path:
        bucket_path = default_path

    # Validate path exists
    if not os.path.isdir(bucket_path):
        print(f"Error: Directory '{bucket_path}' does not exist!")
        input("Press Enter to return to main menu...")
        return

    # Load and run create_schemas module
    try:
        create_schemas_module = load_module("create_schemas.py", "create_schemas")
        if create_schemas_module:
            create_schemas_module.generate_schemas(bucket_path)
    except Exception as e:
        print(f"Error running schema creation: {str(e)}")

    input("\nPress Enter to return to main menu...")


def check_schemas():
    """Run the schema checking process."""
    print_header()
    print("Check BigQuery Schemas")
    print("---------------------")

    # Load and run check_schemas module
    try:
        check_schemas_module = load_module("check_schemas.py", "check_schemas")
        if check_schemas_module:
            check_schemas_module.main()
    except Exception as e:
        print(f"Error running schema check: {str(e)}")

    input("\nPress Enter to return to main menu...")


def replace_schemas():
    """Run the schema replacement process."""
    print_header()
    print("Replace BigQuery Schemas")
    print("---------------------")

    # Get config
    config = get_config()
    
    # Ask for project ID
    default_project = config.get_gcp_project_id()
    project_id = input(
        f"Enter Google Cloud project ID [default: {default_project}]: "
    ).strip()
    if not project_id:
        project_id = default_project

    # Ask for dataset
    default_dataset = config.get_bq_dataset()
    dataset = input(
        f"Enter BigQuery dataset name [default: {default_dataset}]: "
    ).strip()
    if not dataset:
        dataset = default_dataset

    # Ask for schema directory
    default_schema_dir = config.get_schemas_dir()
    schema_dir = input(
        f"Enter path to schema directory [default: {default_schema_dir}]: "
    ).strip()
    if not schema_dir:
        schema_dir = default_schema_dir

    # Validate path exists
    if not os.path.isdir(schema_dir):
        print(f"Error: Directory '{schema_dir}' does not exist!")
        input("Press Enter to return to main menu...")
        return

    # Ask for table filter
    table_filter_input = input(
        "Enter specific table names to process (comma-separated), or leave empty for all: "
    ).strip()
    table_filter = [t.strip() for t in table_filter_input.split(",") if t.strip()] or None

    # Load and run replace_schema_bq module
    try:
        replace_schema_module = load_module("replace_schema_bq.py", "replace_schema_bq")
        if replace_schema_module:
            print(f"Using schema directory: {schema_dir}")
            result = replace_schema_module.replace_bigquery_schemas(
                project_id, dataset, schema_dir, table_filter
            )
            if not result:
                print(
                    "\nSchema replacement encountered errors. Please check the output above."
                )
    except Exception as e:
        print(f"Error replacing schemas: {str(e)}")

    input("\nPress Enter to return to main menu...")


def setup_transfers():
    """Run the BigQuery transfer setup process."""
    print_header()
    print("Setup BigQuery Transfers")
    print("---------------------")

    # Get config
    config = get_config()
    
    # Ask for project ID
    default_project = config.get_gcp_project_id()
    project_id = input(
        f"Enter Google Cloud project ID [default: {default_project}]: "
    ).strip()
    if not project_id:
        project_id = default_project

    # Ask for transfer location
    default_location = config.get_transfer_location()
    location = input(f"Enter transfer location [default: {default_location}]: ").strip()
    if not location:
        location = default_location

    # Ask for dataset
    default_dataset = config.get_bq_dataset()
    dataset = input(
        f"Enter BigQuery dataset name [default: {default_dataset}]: "
    ).strip()
    if not dataset:
        dataset = default_dataset

    # Ask for schema directory
    default_schema_dir = config.get_schemas_dir()
    schema_dir = input(
        f"Enter path to schema directory [default: {default_schema_dir}]: "
    ).strip()
    if not schema_dir:
        schema_dir = default_schema_dir

    # Validate path exists
    if not os.path.isdir(schema_dir):
        print(f"Error: Directory '{schema_dir}' does not exist!")
        input("Press Enter to return to main menu...")
        return

    # Batch processing has been removed as it was not working correctly

    # Ask for S3 bucket
    default_bucket = config.get_s3_bucket()
    s3_bucket = input(
        f"Enter S3 bucket name (without s3:// prefix) [default: {default_bucket}]: "
    ).strip()
    if not s3_bucket:
        s3_bucket = default_bucket

    # Get AWS credentials from config
    access_key, secret_key = config.get_aws_credentials()
    if not access_key or not secret_key:
        print("\n❌ AWS credentials not found in environment variables!")
        print("Please set AWS_ACCESS_KEY_ID and AWS_SECRET_ACCESS_KEY in your .env file")
        input("Press Enter to return to main menu...")
        return
    
    print(f"Using AWS credentials: {access_key[:4]}...{access_key[-4:]}")

    # Ask for file format
    default_format = config.get_csv_format()
    file_format = input(f"Enter file format [default: {default_format}]: ").strip()
    if not file_format:
        file_format = default_format

    # Ask for field delimiter
    default_delimiter = config.get_csv_delimiter()
    delimiter = input(f"Enter field delimiter [default: {default_delimiter}]: ").strip()
    if not delimiter:
        delimiter = default_delimiter

    # Ask for skip leading rows
    default_skip = config.get_skip_leading_rows()
    skip_rows = input(
        f"Enter number of rows to skip [default: {default_skip}]: "
    ).strip()
    if not skip_rows:
        skip_rows = default_skip

    # Ask for write disposition
    default_disposition = config.get_write_disposition()
    disposition = input(
        f"Enter write disposition [default: {default_disposition}]: "
    ).strip()
    if not disposition:
        disposition = default_disposition

    # Ask for test suffix
    default_suffix = "y" if config.get_add_test_suffix() else "n"
    suffix_input = (
        input(f"Add '_test' suffix to table names? (y/n) [default: {default_suffix}]: ")
        .strip()
        .lower()
    )
    test_suffix = suffix_input in ["", "y", "yes"] if suffix_input else config.get_add_test_suffix()

    # Ask for table filter
    table_filter_input = input(
        "Enter specific table names to process (comma-separated), or leave empty for all: "
    ).strip()
    table_filter = [t.strip() for t in table_filter_input.split(",") if t.strip()] or None

    # Load and run setup_transfers_bq module
    try:
        transfers_module = load_module("setup_transfers_bq.py", "setup_transfers_bq")
        if transfers_module:
            print(f"Using schema directory: {schema_dir}")
            result = transfers_module.setup_transfers(
                project_id,
                location,
                dataset,
                schema_dir,
                s3_bucket,
                access_key,
                secret_key,
                file_format,
                delimiter,
                skip_rows,
                disposition,
                test_suffix,
                table_filter,
            )
            if not result:
                print(
                    "\nTransfer setup encountered errors. Please check the output above."
                )
    except Exception as e:
        print(f"Error setting up transfers: {str(e)}")

    input("\nPress Enter to return to main menu...")


def copy_s3_bucket():
    """Run the S3 bucket copy process."""
    print_header()
    print("Copy S3 Bucket Contents to Local Directory")
    print("-----------------------------------------")

    # Get config
    config = get_config()
    
    # Ask for S3 bucket
    default_bucket = config.get_s3_bucket()
    s3_bucket = input(
        f"Enter S3 bucket name (without s3:// prefix) [default: {default_bucket}]: "
    ).strip()
    if not s3_bucket:
        s3_bucket = default_bucket

    # Get AWS credentials from config
    access_key, secret_key = config.get_aws_credentials()
    if not access_key or not secret_key:
        print("\n❌ AWS credentials not found in environment variables!")
        print("Please set AWS_ACCESS_KEY_ID and AWS_SECRET_ACCESS_KEY in your .env file")
        input("Press Enter to return to main menu...")
        return
    
    print(f"Using AWS credentials: {access_key[:4]}...{access_key[-4:]}")

    # Ask for local directory
    default_dir = config.get_local_bucket_dir()
    local_dir = input(
        f"Enter local directory to copy to [default: {default_dir}]: "
    ).strip()
    if not local_dir:
        local_dir = default_dir

    # Load and run copy_s3_bucket module
    try:
        copy_module = load_module("copy_s3_bucket.py", "copy_s3_bucket")
        if copy_module:
            result = copy_module.copy_s3_bucket(
                s3_bucket=s3_bucket,
                destination_dir=local_dir,
                aws_access_key_id=access_key,
                aws_secret_access_key=secret_key,
            )
            if not result:
                print(
                    "\nS3 bucket copy encountered errors. Please check the output above."
                )
    except Exception as e:
        print(f"Error copying S3 bucket: {str(e)}")

    input("\nPress Enter to return to main menu...")


def check_csv_structure():
    """Run the CSV structure checking process."""
    print_header()
    print("Check CSV Structure")
    print("-----------------")
    
    # Get config
    config = get_config()
    
    # Ask for CSV file or directory
    default_path = config.get_local_bucket_dir()
    csv_path = input(f"Enter path to CSV file or directory [default: {default_path}]: ").strip()
    if not csv_path:
        csv_path = default_path
    
    # Check if it's a file or directory
    if os.path.isfile(csv_path):
        files_to_check = [csv_path]
    elif os.path.isdir(csv_path):
        files_to_check = [os.path.join(csv_path, f) for f in os.listdir(csv_path) 
                         if f.endswith('.csv') and os.path.isfile(os.path.join(csv_path, f))]
        if not files_to_check:
            print(f"No CSV files found in {csv_path}")
            input("\nPress Enter to return to main menu...")
            return
    else:
        print(f"Error: Path '{csv_path}' does not exist!")
        input("\nPress Enter to return to main menu...")
        return
    
    # Ask for delimiter
    default_delimiter = config.get_csv_delimiter()
    delimiter = input(f"Enter CSV delimiter [default: {default_delimiter}]: ").strip()
    if not delimiter:
        delimiter = default_delimiter
    
    # Ask if all rows should be checked
    check_all = input("Check all rows for consistency? (y/n) [default: y]: ").strip().lower()
    check_all = check_all in ["", "y", "yes"]
    
    # Run the check for each file
    try:
        check_module = load_module("check_csv_structure.py", "check_csv_structure")
        if check_module:
            for file in files_to_check:
                print(f"\n===== Checking {file} =====")
                check_module.analyze_csv_file(file, delimiter, check_all)
    except Exception as e:
        print(f"Error checking CSV structure: {str(e)}")
    
    input("\nPress Enter to return to main menu...")

def fix_csv_newlines():
    """Run the CSV newline fixing process."""
    print_header()
    print("Fix CSV Newlines")
    print("---------------")
    
    # Get config
    config = get_config()
    
    # Ask for CSV file or directory
    default_path = config.get_local_bucket_dir()
    csv_path = input(f"Enter path to CSV file or directory [default: {default_path}]: ").strip()
    if not csv_path:
        csv_path = default_path
    
    # Check if it's a file or directory
    if os.path.isfile(csv_path):
        files_to_fix = [csv_path]
    elif os.path.isdir(csv_path):
        files_to_fix = [os.path.join(csv_path, f) for f in os.listdir(csv_path) 
                       if f.endswith('.csv') and os.path.isfile(os.path.join(csv_path, f))]
        if not files_to_fix:
            print(f"No CSV files found in {csv_path}")
            input("\nPress Enter to return to main menu...")
            return
    else:
        print(f"Error: Path '{csv_path}' does not exist!")
        input("\nPress Enter to return to main menu...")
        return
    
    # Ask for delimiter
    default_delimiter = config.get_csv_delimiter()
    delimiter = input(f"Enter CSV delimiter [default: {default_delimiter}]: ").strip()
    if not delimiter:
        delimiter = default_delimiter
    
    # Ask for output directory
    default_output = config.get_fixed_bucket_dir()
    output_dir = input(f"Enter output directory for fixed files [default: {default_output}]: ").strip()
    if not output_dir:
        output_dir = default_output
    
    # Create output directory if it doesn't exist
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
    
    # Run the fix for each file
    try:
        fix_module = load_module("fix_csv_newlines.py", "fix_csv_newlines")
        if fix_module:
            for file in files_to_fix:
                filename = os.path.basename(file)
                output_file = os.path.join(output_dir, filename)
                print(f"\n===== Fixing {filename} =====")
                fix_module.fix_csv_newlines(file, output_file, delimiter)
    except Exception as e:
        print(f"Error fixing CSV newlines: {str(e)}")
    
    input("\nPress Enter to return to main menu...")

def main_menu():
    """Display the main menu and handle user input."""
    while True:
        print("\nBigQuery Migration Helper")
        print("=========================")
        print("1. Copy S3 Bucket Contents to Local Directory")
        print("2. Create BigQuery Schemas from CSV files")
        print("3. Check Schemas against CSV files")
        print("4. Replace BigQuery Tables with Schemas")
        print("5. Setup BigQuery Transfers from S3")
        print("6. Check CSV Structure")
        print("7. Fix CSV Newlines")
        print("8. Exit")

        choice = input("\nEnter your choice (1-8): ").strip()

        if choice == "1":
            copy_s3_bucket()
        elif choice == "2":
            create_schemas()
        elif choice == "3":
            check_schemas()
        elif choice == "4":
            replace_schemas()
        elif choice == "5":
            setup_transfers()
        elif choice == "6":
            check_csv_structure()
        elif choice == "7":
            fix_csv_newlines()
        elif choice == "8":
            print("\nExiting program...")
            break
        else:
            print("\nInvalid choice. Please try again.")
            input("Press Enter to continue...")

if __name__ == "__main__":
    main_menu()
