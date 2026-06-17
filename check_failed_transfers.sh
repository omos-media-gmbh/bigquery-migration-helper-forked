#!/bin/bash
# Daily check for failed BigQuery data transfers.
# Posts to Slack #dbt-workflows if any transfers failed in the past 24 hours.
#
# Setup:
#   1. Create a Slack incoming webhook at https://api.slack.com/apps → Your App → Incoming Webhooks
#   2. Set the SLACK_WEBHOOK_URL below or export it as an environment variable
#   3. Add to crontab: crontab -e → 0 8 * * * /path/to/check_failed_transfers.sh
#
# Requires: bq CLI (gcloud SDK), curl, python3

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"

# Load .env file if it exists
if [ -f "$SCRIPT_DIR/.env" ]; then
    export $(grep -v '^#' "$SCRIPT_DIR/.env" | grep -v '^$' | xargs)
fi

SLACK_WEBHOOK_URL="${SLACK_WEBHOOK_URL:-}"
PROJECT_ID="${GCP_PROJECT_ID:-metaflow-data}"
TRANSFER_LOCATION="europe"

if [ -z "$SLACK_WEBHOOK_URL" ]; then
    echo "Error: SLACK_WEBHOOK_URL is not set."
    echo "Set it in your .env file or export it as an environment variable."
    exit 1
fi

# Get all transfer configs
TRANSFERS=$(bq ls --transfer_config --transfer_location="$TRANSFER_LOCATION" --project_id="$PROJECT_ID" --format=json 2>/dev/null)

if [ -z "$TRANSFERS" ] || [ "$TRANSFERS" = "[]" ]; then
    echo "No transfers found or bq command failed."
    exit 1
fi

# Find failed transfers
FAILED=$(echo "$TRANSFERS" | python3 -c "
import json, sys

data = json.load(sys.stdin)
failed = [t for t in data if t.get('state') == 'FAILED']

if not failed:
    sys.exit(1)

for t in sorted(failed, key=lambda x: x.get('displayName', '')):
    name = t.get('displayName', 'unknown')
    updated = t.get('updateTime', 'unknown')
    config_id = t.get('name', '').split('/')[-1]
    print(f'{name}|{updated}|{config_id}')
" 2>/dev/null)

if [ -z "$FAILED" ]; then
    echo "$(date): All transfers healthy ✅"
    exit 0
fi

# Build Slack message
FAIL_COUNT=$(echo "$FAILED" | wc -l | tr -d ' ')
TABLE_ROWS=""
while IFS='|' read -r name updated config_id; do
    TABLE_ROWS="${TABLE_ROWS}| ${name} | ${updated} |\n"
done <<< "$FAILED"

MESSAGE=$(cat <<EOF
🚨 *BigQuery Data Transfers Alert* — ${FAIL_COUNT} failed BigQuery data transfer(s) detected

| Table | Last Updated |
|-------|-------------|
$(echo -e "$TABLE_ROWS")

Run \`fix_tables.py\` to fix:
\`\`\`bash
cd /Users/lay/omos_da/metaflow/bigquery-migration-helper
python3 fix_tables.py <table_names>
\`\`\`
EOF
)

# Post to Slack
curl -s -X POST -H 'Content-type: application/json' \
    --data "$(python3 -c "import json; print(json.dumps({'text': '''$MESSAGE'''}))")" \
    "$SLACK_WEBHOOK_URL"

echo "$(date): Posted ${FAIL_COUNT} failure(s) to Slack"
