# Backup & Restore

FastCMS provides database backup and restore functionality to protect your data and enable disaster recovery.

## What Gets Backed Up?

A backup includes:
- Database file (`app.db`)
- Uploaded files (in `data/files/`)
- Complete system state at backup time

## Creating a Backup

**Via API:**
```bash
curl -X POST "http://localhost:8000/api/v1/backups" \
  -H "Authorization: Bearer ADMIN_TOKEN"
```

**Response:**
```json
{
  "filename": "backup_20250115_100000.zip",
  "size_bytes": 1048576,
  "created": "2025-01-15T10:00:00",
  "path": "data/backups/backup_20250115_100000.zip"
}
```

**Via Admin Dashboard:**
1. Navigate to `/admin/backups`
2. Click "Create Backup"
3. Download the backup file

## Listing Backups

```bash
curl "http://localhost:8000/api/v1/backups" \
  -H "Authorization: Bearer ADMIN_TOKEN"
```

**Response:**
```json
{
  "items": [
    {
      "filename": "backup_20250115_100000.zip",
      "name": "backup_20250115_100000",
      "size_mb": 1.5,
      "created": "2025-01-15T10:00:00"
    }
  ],
  "total": 1
}
```

## Restoring from a Backup

**IMPORTANT:** Restore requires server restart to complete.

**Step 1: Stage the restore**
```bash
curl -X POST "http://localhost:8000/api/v1/backups/{filename}/restore" \
  -H "Authorization: Bearer ADMIN_TOKEN"
```

**Response:**
```json
{
  "status": "pending_restart",
  "message": "Backup staged for restore. Please restart the server to complete restoration.",
  "backup_filename": "backup_20250115_100000.zip"
}
```

**Step 2: Restart the server**
```bash
# Stop the server (Ctrl+C or kill the process)
# Start the server again
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

On startup, the server will:
1. Detect the pending restore
2. Backup the current database to `.db.before_restore`
3. Replace the database with the backup
4. Restore all files
5. Complete the restore and remove the staging marker

## How Restore Works

The restore process uses a "restore on restart" pattern to avoid database locking issues:

1. **Staging Phase** (when you call the restore endpoint):
   - Extracts backup to `data/backups/restore_staging/`
   - Creates a marker file `.restore_pending` with metadata
   - Returns immediately

2. **Execution Phase** (on server startup):
   - Checks for `.restore_pending` marker
   - Backs up current database to prevent data loss
   - Replaces database and files from staging
   - Cleans up staging directory and marker
   - Application starts with restored data

This approach ensures:
- No database locking conflicts
- Safe restoration without corruption
- Automatic rollback if restore fails

## Deleting a Backup

```bash
curl -X DELETE "http://localhost:8000/api/v1/backups/{filename}" \
  -H "Authorization: Bearer ADMIN_TOKEN"
```

## Backup Storage

**Default Location:** `data/backups/`

**Filename Format:** `backup_YYYYMMDD_HHMMSS.zip`

**Backup Contents:**
- `database.db` - Complete SQLite database
- `files/` - All uploaded files
- `metadata.json` - Backup metadata (timestamp, app version, backup name)

## Best Practices

1. **Regular Schedule**: Backup daily or before major changes
2. **Retention Policy**: Keep at least 7 daily, 4 weekly, 12 monthly backups
3. **Test Restores**: Monthly test restore to verify backups work
4. **Off-site Storage**: Copy backups to cloud storage (S3, Google Cloud Storage)
5. **Monitor Space**: Ensure adequate disk space for backups

## Automated Backups

**Linux/Mac (cron):**
```bash
# Add to crontab: Daily backup at 2 AM
0 2 * * * curl -X POST http://localhost:8000/api/v1/backups \
  -H "Authorization: Bearer $ADMIN_TOKEN"
```

**Python script:**
```python
import requests
import schedule
import time

def create_backup():
    response = requests.post(
        'http://localhost:8000/api/v1/backups',
        headers={'Authorization': 'Bearer YOUR_ADMIN_TOKEN'}
    )
    if response.status_code == 200:
        print(f"Backup created: {response.json()['filename']}")
    else:
        print(f"Backup failed: {response.text}")

# Run daily at 2 AM
schedule.every().day.at("02:00").do(create_backup)

while True:
    schedule.run_pending()
    time.sleep(60)
```

## Disaster Recovery

**Scenario: Complete data loss**

1. Stop the FastCMS application
2. Locate your most recent backup file
3. Extract the backup:
   ```bash
   unzip data/backups/backup_20250115_100000.zip -d data/backups/restore_staging
   ```
4. Replace database:
   ```bash
   cp data/backups/restore_staging/database.db data/app.db
   ```
5. Restore files:
   ```bash
   cp -r data/backups/restore_staging/files/* data/files/
   ```
6. Restart FastCMS
7. Verify all data is restored

**Scenario: Accidental deletion**

1. Create a backup of current state (just in case)
2. Identify the backup before the deletion occurred
3. Use the restore API endpoint
4. Restart the server
5. Verify the deleted data is back
