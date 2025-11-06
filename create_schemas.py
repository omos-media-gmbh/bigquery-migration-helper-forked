import csv
import json
import os
import re
from config_loader import get_config


def detect_date_type_from_sample(sample_values):
    """Detect if date values are DATE or TIMESTAMP by examining sample data."""
    timestamp_pattern = re.compile(r"\d{4}-\d{2}-\d{2}\s+\d{2}:\d{2}")
    date_only_pattern = re.compile(r"^\d{4}-\d{2}-\d{2}$")

    for value in sample_values:
        if value and value.strip():
            value = value.strip()
            if timestamp_pattern.search(value):
                return "TIMESTAMP"
            elif date_only_pattern.match(value):
                return "DATE"

    return "STRING"


def detect_type_column(sample_values):
    """Detect if 'type' column contains integers or strings."""
    for value in sample_values:
        if value and value.strip():
            value = value.strip()
            # Check if value is numeric (integer)
            if value.isdigit() or (value.startswith("-") and value[1:].isdigit()):
                return "INTEGER"
            # If we find a non-numeric value, it's a string
            else:
                return "STRING"
    
    return "STRING"


def infer_data_type(column_name, sample_values=None):
    """Infer BigQuery data type from column name and sample values."""
    column_name = column_name.lower()

    # Type field: sample data to distinguish INTEGER vs STRING
    if column_name == "type":
        if sample_values:
            return detect_type_column(sample_values)
        return "STRING"

    # Date fields: sample data to distinguish DATE vs TIMESTAMP
    elif column_name == "date":
        if sample_values:
            return detect_date_type_from_sample(sample_values)
        return "TIMESTAMP"

    elif any(
        date_term == column_name or column_name.endswith(date_term)
        for date_term in ["birth_date", "birth_day", "hidden_at_dashboard", "hidden_at"]
    ):
        if sample_values:
            detected_type = detect_date_type_from_sample(sample_values)
            if detected_type in ["DATE", "TIMESTAMP"]:
                return detected_type
        return "DATE"

    elif column_name in ["breakfast", "lunch", "dinner"]:
        return "TIME"

    # Timestamp fields
    elif any(
        date_term in column_name
        for date_term in [
            "created_at",
            "updated_at",
            "timestamp",
            "last_login",
            "migrated_at",
            "onboarded_at",
            "deleted_at",
            "beta_phase_start",
            "start_phase_one",
            "token_last_updated",
            "date_joined",
        ]
    ):
        return "TIMESTAMP"

    elif any(
        bool_term == column_name or column_name.startswith(bool_term)
        for bool_term in ["is_", "has_", "shake_", "show_"]
    ):
        return "BOOLEAN"

    elif column_name in ["active", "enabled"]:
        return "BOOLEAN"

    elif any(int_term == column_name for int_term in ["gender", "phase", "position"]):
        return "INTEGER"

    elif column_name == "email" or "email" in column_name:
        return "STRING"

    elif any(
        rel_term in column_name
        for rel_term in ["groups", "permissions", "user_set", "related_"]
    ):
        return "STRING"

    elif column_name == "id" or column_name.endswith("_id"):
        return "STRING"

    elif any(
        term in column_name
        for term in [
            "image",
            "url",
            "path",
            "file",
            "link",
            "flag",
            "token",
            "password",
            "name",
            "address",
        ]
    ):
        return "STRING"

    elif any(
        numeric_term == column_name or column_name.startswith(numeric_term)
        for numeric_term in ["start_"]
    ):
        return "NUMERIC"

    elif column_name in [
        "count",
        "amount",
        "total",
        "price",
        "quantity",
        "weight",
        "age",
        "height",
        "calories",
        "hip",
        "waist",
        "chest",
        "belly",
        "target_weight",
        "quantity",
        "quantity_one",
        "quantity_two",
        "unit_one",
        "unit_two",
        "calorie",
        "carbohydrates",
        "protein",
        "fat",
        "sugar",
        "preparation_quantity",
        "preparation_time",
        "difficulty",
        "baking_time",
        "cooling_time",
        "rest_time",
    ]:
        return "NUMERIC"

    elif any(
        integer_term == column_name or column_name.startswith(integer_term)
        for integer_term in ["number_", "number"]
    ):
        return "INTEGER"

    elif column_name in [
        "sleep",
        "freetime",
        "work",
        "sports",
        "points",
        "points_upon_reached",
        "required_points",
    ]:
        return "INTEGER"

    return "STRING"


def get_bigquery_schema(csv_path: str, delimiter=";", sample_rows=100):
    """Generate BigQuery schema from CSV file by sampling data."""
    with open(csv_path, "r") as f:
        first_line = f.readline().strip()
        if ";" in first_line and "," not in first_line:
            delimiter = ";"

        f.seek(0)
        reader = csv.reader(f, delimiter=delimiter)
        headers = next(reader)

        # Sample data for type detection
        sample_data = []
        for i, row in enumerate(reader):
            if i >= sample_rows:
                break
            sample_data.append(row)

        schema = []
        for col_idx, header in enumerate(headers):
            header = header.strip()
            if header:
                sample_values = [
                    row[col_idx] if col_idx < len(row) else "" for row in sample_data
                ]
                data_type = infer_data_type(header, sample_values)

                # Only 'id' column is REQUIRED, foreign keys can be nullable
                mode = "REQUIRED" if header.lower() == "id" else "NULLABLE"
                field_schema = {"name": header, "type": data_type, "mode": mode}
                schema.append(field_schema)

        return schema


def generate_schemas(bucket_path=None, schema_dir=None):
    """Generate BigQuery schemas from CSV files in the specified bucket path."""
    config = get_config()
    if not bucket_path:
        bucket_path = config.get_local_bucket_dir()
    if not schema_dir:
        schema_dir = config.get_schemas_dir()

    print(f"\nBucket path: {bucket_path}")

    if not os.path.isdir(bucket_path):
        print(f"Error: Directory '{bucket_path}' does not exist!")
        return False

    csv_files = [f for f in os.listdir(bucket_path) if f.endswith(".csv")]
    print(f"Processing {len(csv_files)} files")

    if not csv_files:
        print("No CSV files found in the specified directory.")
        return False

    os.makedirs(schema_dir, exist_ok=True)

    for filename in csv_files:
        csv_path = os.path.join(bucket_path, filename)
        schema = get_bigquery_schema(csv_path)
        print(f"\n{filename}:")

        schema_filename = os.path.splitext(filename)[0] + ".json"
        schema_path = os.path.join(schema_dir, schema_filename)

        with open(schema_path, "w") as schema_file:
            json.dump(schema, schema_file, indent=2)

        print(f"Schema saved to {schema_path}")

    return True


if __name__ == "__main__":
    generate_schemas()
