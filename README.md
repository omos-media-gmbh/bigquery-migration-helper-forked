# BigQuery Migration Helper (Fork)

> **This is a fork of [patrk-omos/bigquery-migration-helper](https://github.com/patrk-omos/bigquery-migration-helper)** with added tooling for monitoring and fixing broken BigQuery data transfers.

## What this fork adds

- **Table-specific fixes**: Replace schemas and transfers for specific tables without touching the rest of the dataset (via `table_filter` in menu options 4 and 5)
- **One-command fix script**: `fix_tables.py` — downloads CSV from S3, regenerates the schema, and replaces the BQ table in a single command
- **Automated failure monitoring**: A GitHub Actions workflow that runs daily at 9:30 CET, checks for failed BigQuery data transfers, diagnoses schema mismatches (comparing S3 CSV headers against BQ table schemas), and posts alerts to Slack
- **Configurable transfer schedule**: Transfer schedule now uses `config.json` instead of being hardcoded

### Quick fix for broken tables

```bash
python3 fix_tables.py account_userprofile community_group
```

This downloads the CSVs from S3, regenerates schemas, and replaces only the specified BQ tables. Existing transfers pick up the new schema on their next scheduled run — no need to recreate them.

### GitHub Actions monitoring

The workflow at `.github/workflows/check_failed_transfers.yml` requires these repository secrets:
- `GCP_SERVICE_ACCOUNT_KEY` — GCP service account JSON key with BigQuery permissions
- `SLACK_WEBHOOK_URL` — Slack incoming webhook for the alerts channel
- `AWS_ACCESS_KEY_ID` — AWS access key (read-only, for downloading CSV headers to diagnose mismatches)
- `AWS_SECRET_ACCESS_KEY` — AWS secret key

---

## Original README

A comprehensive Python tool for migrating CSV data from AWS S3 to Google Cloud BigQuery. This tool automates the entire migration pipeline including data extraction, schema generation, validation, and transfer setup.

## Features

- **S3 Data Extraction**: Copy CSV files from AWS S3 buckets to local storage
- **Smart Schema Generation**: Automatically generate BigQuery schemas from CSV files with intelligent data type inference
- **Data Validation**: Analyze CSV structure and validate data integrity
- **Schema Management**: Create, replace, and validate BigQuery table schemas
- **Automated Transfers**: Set up scheduled data transfer pipelines from S3 to BigQuery
- **CSV Processing**: Fix formatting issues like embedded newlines and structural problems
- **Interactive CLI**: User-friendly command-line interface with guided workflows

## 📋 Prerequisites

- **Python 3.6+**
- **Google Cloud SDK** (`gcloud` CLI tool)
- **BigQuery CLI** (`bq` command)
- **AWS CLI** (`aws` command)
- **Authentication**:
  - Google Cloud credentials configured (`gcloud auth login`)
  - AWS credentials configured (`aws configure` or environment variables)

## 🛠️ Installation

1. Clone or download this repository
2. **Create and activate a virtual environment** (recommended):
   ```bash
   # Create virtual environment
   python3 -m venv venv
   
   # Activate virtual environment
   # On macOS/Linux:
   source venv/bin/activate
   # On Windows:
   # venv\Scripts\activate
   ```
3. Install Python dependencies:
   ```bash
   pip install -r requirements.txt
   ```
4. Ensure all prerequisites are installed (Google Cloud SDK, AWS CLI, etc.)
5. **Configure credentials and settings** (see Configuration section below)
6. Run the main script:
   ```bash
   python3 main.py
   ```

### Quick Setup (Copy-Paste Ready)
```bash
# Setup virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Setup configuration
cp .env.example .env
# Edit .env with your AWS credentials

# Run the tool
python3 main.py
```

## 📖 Usage

### Interactive Mode

Run the main script to access the interactive menu:

```bash
python3 main.py
```

The tool provides 7 main functions:

### 1. Copy S3 Bucket Contents to Local Directory
- Downloads all files from an S3 bucket to a local directory
- Requires AWS credentials
- Default local directory: `./bucket`

### 2. Create BigQuery Schemas from CSV Files
- Analyzes CSV files and generates BigQuery JSON schemas
- Intelligent data type inference based on column names and patterns
- Supports custom delimiters (default: semicolon `;`)
- Outputs schemas to `./schemas/` directory

#### Supported Data Types:
- **DATE**: For date fields (`date`, `birth_date`, etc.)
- **TIME**: For time fields (`breakfast`, `lunch`, `dinner`)
- **TIMESTAMP**: For datetime fields (`created_at`, `updated_at`, etc.)
- **BOOLEAN**: For boolean fields (prefixed with `is_`, `has_`, etc.)
- **INTEGER**: For integer fields (`phase`, `position`, etc.)
- **NUMERIC**: For decimal fields (`weight`, `calories`, `amount`, etc.)
- **STRING**: For text fields and IDs (default)

### 3. Check Schemas against CSV Files
- Validates generated schemas against actual CSV data
- Identifies structural inconsistencies
- Reports column count mismatches

### 4. Replace BigQuery Tables with Schemas
- Deletes existing BigQuery tables and recreates them with new schemas
- Batch processes all schema files in the schemas directory

### 5. Setup BigQuery Transfers from S3
- Creates automated data transfer configurations
- Schedules daily transfers from S3 to BigQuery (default: every day at 00:30)
- Supports custom transfer parameters:
  - File format (default: CSV)
  - Field delimiter (default: `;`)
  - Skip leading rows (default: 1)
  - Write disposition (default: WRITE_TRUNCATE)
- Option to add `_test` suffix to table names

### 6. Check CSV Structure
- Analyzes CSV file structure and integrity
- Detects delimiter types automatically
- Identifies multi-line fields and structural issues
- Can check individual files or entire directories
- Options for comprehensive row-by-row validation

### 7. Fix CSV Newlines
- Fixes CSV files with embedded newline characters
- Preserves data integrity while cleaning structure
- Outputs cleaned files to `./bucket_fixed/` directory
- Batch processes multiple files

## 🔧 Command Line Usage

Each module can also be run independently:

```bash
# Copy S3 bucket
python3 copy_s3_bucket.py --bucket your-bucket --destination ./local-dir

# Generate schemas
python3 create_schemas.py

# Check CSV structure
python3 check_csv_structure.py path/to/file.csv --delimiter ";" --all-rows

# Fix CSV newlines
python3 fix_csv_newlines.py

# Replace BigQuery schemas
python3 replace_schema_bq.py project-id dataset-name ./schemas

# Setup transfers
python3 setup_transfers_bq.py project-id dataset-name ./schemas bucket-name
```

## 📁 Project Structure

```
bigquery-migration-helper/
├── main.py                    # Interactive CLI interface
├── config_loader.py          # Configuration management
├── copy_s3_bucket.py         # S3 data extraction
├── create_schemas.py         # Schema generation
├── check_csv_structure.py    # CSV validation
├── check_schemas.py          # Schema validation
├── fix_csv_newlines.py       # CSV cleaning
├── fix_tables.py             # One-command table fix (fork addition)
├── replace_schema_bq.py      # BigQuery table management
├── setup_transfers_bq.py     # Transfer configuration
├── check_failed_transfers.sh # Local transfer failure check (fork addition)
├── .github/workflows/        # GitHub Actions (fork addition)
│   └── check_failed_transfers.yml  # Daily transfer monitoring
├── config.json               # Configuration settings
├── .env.example              # Environment variable template
├── .env                      # Your credentials (create from .env.example)
├── requirements.txt          # Python dependencies
├── .gitignore                # Git ignore rules
├── venv/                     # Virtual environment (created by you)
├── bucket/                   # Local CSV files
├── bucket_fixed/            # Cleaned CSV files
├── schemas/                 # Generated BigQuery schemas
└── README.md               # This file
```

## ⚙️ Configuration

### Environment Variables (.env file)

1. **Copy the template**:
   ```bash
   cp .env.example .env
   ```

2. **Edit .env with your actual values** (all are required):
   ```bash
   # AWS Credentials (REQUIRED)
   AWS_ACCESS_KEY_ID=your_actual_aws_access_key
   AWS_SECRET_ACCESS_KEY=your_actual_aws_secret_key
   
   # Google Cloud Project Settings (REQUIRED)
   GCP_PROJECT_ID=your-gcp-project-id
   BQ_DATASET=your-bigquery-dataset-name
   TRANSFER_LOCATION=eu
   
   # AWS S3 Settings (REQUIRED)
   S3_BUCKET=your-s3-bucket-name
   
   # Google Cloud Service Account (optional - if not using gcloud auth)
   # GOOGLE_APPLICATION_CREDENTIALS=/path/to/service-account.json
   ```

### Configuration File (config.json)

The tool uses `config.json` for non-sensitive settings:

```json
{
  "paths": {
    "local_bucket_dir": "./bucket",
    "fixed_bucket_dir": "./bucket_fixed",
    "schemas_dir": "./schemas"
  },
  "csv": {
    "default_delimiter": ";",
    "file_format": "CSV",
    "skip_leading_rows": "1",
    "write_disposition": "WRITE_TRUNCATE"
  },
  "transfer": {
    "schedule": "every day 00:30",
    "add_test_suffix": true
  }
}
```

**Note**: Sensitive information like project IDs, dataset names, and S3 bucket names are now stored in the `.env` file for better security.

### Customization Priority

1. **Environment variables** (highest priority)
2. **config.json values**
3. **Interactive prompts** (can override both)
4. **Built-in defaults** (fallback)

You can customize settings by:
- Editing `config.json` for permanent changes
- Setting environment variables for credential overrides
- Using interactive prompts for one-time changes

## 🔍 Data Type Inference Logic

The schema generator uses intelligent rules to infer BigQuery data types:

- **Exact matches**: `id`, `email`, `date` → specific types
- **Pattern matching**: Fields ending with `_at`, `_id` → TIMESTAMP, STRING
- **Prefix matching**: Fields starting with `is_`, `has_` → BOOLEAN
- **Content-based**: Fields containing `weight`, `calories` → NUMERIC
- **Default fallback**: All unknown fields → STRING

## 🔒 Security

- **Never commit .env files**: The `.env` file contains sensitive credentials and should never be committed to version control
- **Use .env.example**: Share the `.env.example` template instead of actual credentials
- **Secure credential storage**: Consider using cloud secret management services for production environments
- **File permissions**: Ensure `.env` file has restricted permissions (`chmod 600 .env`)

## 🚨 Important Notes

- **Authentication required**: Ensure both Google Cloud and AWS credentials are properly configured
- **Data backup**: Always backup your data before running destructive operations
- **Schema validation**: Review generated schemas before applying them to production tables
- **Transfer costs**: Be aware of data transfer costs between AWS and Google Cloud
- **Rate limits**: Large datasets may hit API rate limits during transfers
- **Credential management**: AWS credentials are now loaded from environment variables for better security

## 🔧 Troubleshooting

### Common Issues

1. **Authentication errors**: Run `gcloud auth login` and `aws configure`
2. **Permission errors**: Ensure proper IAM permissions for BigQuery and S3
3. **CSV parsing errors**: Check delimiter settings and file encoding
4. **Schema mismatches**: Validate CSV structure before schema generation
5. **Transfer failures**: Check AWS credentials and S3 bucket permissions

### Debug Mode

For detailed error information, check the console output during execution. Each operation provides comprehensive logging.

## 📄 License

This project is provided as-is for internal use. Modify and distribute according to your organization's policies.

## 🤝 Contributing

This is a utility tool for data migration. Feel free to extend functionality or improve error handling based on your specific use cases.
