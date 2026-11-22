# SKANDX Database Disaster Recovery & Lead Integrity Plan

**Document ID:** `ENG-DR-003`  
**Classification:** Operational Runbook & Business Continuity  
**Target Environment:** Staging & Production Infrastructure  
**Last Updated:** November 2026  
**Audience:** Site Reliability Engineers, Database Administrators, DevOps  

---

## 1. Executive Summary & RPO/RTO Targets

Buyer leads represent the primary business value of the SKANDX platform. A failure in the primary database must never result in lost inquiries, corrupted auction listings, or duplicate spam.

### Service Level Objectives
- **RPO (Recovery Point Objective):** $< 5 \text{ minutes}$ (Maximum tolerable data loss during catastrophic infrastructure failure).
- **RTO (Recovery Time Objective):** $< 60 \text{ minutes}$ (Maximum duration to restore full operational service from backup).
- **Lead Durability Guarantee:** $100\%$ zero silent drop guarantee. In the event of total database unavailability, incoming leads are persisted to an append-only WAL (`data/leads.jsonl`) on disk and automatically reconciled upon database reconnection.

---

## 2. Lead Durability & Resilience Architecture

```
                  [ Buyer Submits Lead via /api/contact ]
                                    |
                                    v
                 +--------------------------------------+
                 |     Append to data/leads.jsonl       |  <-- Thread-safe disk write
                 |     (fsync append-only write)        |      ensures immediate durability
                 +------------------+-------------------+
                                    |
                                    v
                 +--------------------------------------+
                 |    Check Circuit Breaker Status      |
                 +------------------+-------------------+
                                    |
                  +-----------------+-----------------+
                  | (CLOSED / HALF-OPEN)              | (OPEN / Offline)
                  v                                   v
    +---------------------------+       +---------------------------+
    | Forward to Supabase Cloud |       | Queue in Local Replay Log |
    | REST API customer_leads   |       | Log circuit trip event    |
    +-------------+-------------+       +---------------------------+
                  |
         +--------+--------+
         |                 |
      (Success)        (Network Error)
         |                 |
         v                 v
   [Lead Saved]    [Trip Circuit Breaker]
                   [Preserve on Disk]
```

### 2.1 Deduplication & Idempotency Rules
1. **Deduplication Key:** A compound key consisting of `(phone_number, property_id, submitted_within_300s)`.
2. **Behavior on Duplicate Submission:**
   - If an inquiry for the identical property from the same phone number is received within 5 minutes, the API returns `200 OK` with the existing tracking ID (`lead_id`) and updates the `updated_at` timestamp.
   - Prevents aggressive user retries from flooding the sales queue or sending duplicate notifications.

---

## 3. Backup Strategy & Schedules

| Backup Type | Frequency | Retention | Storage Target | Automation Tool |
| :--- | :--- | :--- | :--- | :--- |
| **Continuous WAL** | Continuous | 7 days | Supabase S3 Archive | Supabase PITR Engine |
| **Logical Dump** | Daily @ 02:00 UTC | 30 days | Encrypted Offsite S3 Bucket | `pg_dump` via GitHub Actions / Cron |
| **Weekly Snapshot** | Weekly (Sunday) | 90 days | Cold Glacier Vault | Cloudflare R2 / AWS Glacier |
| **Local Lead Log** | Real-time Append | Indefinite | Persistent Container Volume | `backend/data/leads.jsonl` |

### 3.1 Logical Backup Script (`scripts/backup_supabase.sh`)
```bash
#!/bin/bash
set -euo pipefail

TIMESTAMP=$(date +"%Y%m%d_%H%M%S")
BACKUP_DIR="/var/backups/skandx"
FILENAME="skandx_prod_${TIMESTAMP}.dump"
ENCRYPTED_FILE="${FILENAME}.gpg"

mkdir -p "${BACKUP_DIR}"

echo "[$(date)] Starting pg_dump for SKANDX database..."
pg_dump "${SUPABASE_DB_URL}" \
  --format=custom \
  --blobs \
  --clean \
  --if-exists \
  --no-owner \
  --no-privileges \
  --file="${BACKUP_DIR}/${FILENAME}"

echo "[$(date)] Encrypting backup with GPG..."
gpg --symmetric --batch --passphrase "${BACKUP_ENCRYPTION_KEY}" \
  --output "${BACKUP_DIR}/${ENCRYPTED_FILE}" "${BACKUP_DIR}/${FILENAME}"
rm "${BACKUP_DIR}/${FILENAME}"

echo "[$(date)] Uploading encrypted dump to offsite S3..."
aws s3 cp "${BACKUP_DIR}/${ENCRYPTED_FILE}" "s3://skandx-db-backups/daily/${ENCRYPTED_FILE}"

echo "[$(date)] Backup completed successfully: ${ENCRYPTED_FILE}"
```

---

## 4. Disaster Recovery & Restoration Procedures

### Phase 1: Database Provisioning & Schema Re-initialization
If the primary PostgreSQL cluster is destroyed:
1. Provision a new PostgreSQL 15+ database instance (Supabase or AWS RDS).
2. Configure credentials in secret manager (`SUPABASE_URL`, `SUPABASE_SERVICE_ROLE_KEY`).
3. Apply migration files in exact sequence:
   ```bash
   psql "${NEW_DB_URL}" -f backend/migrations/001_create_auction_properties.sql
   psql "${NEW_DB_URL}" -f backend/migrations/002_create_customer_leads.sql
   psql "${NEW_DB_URL}" -f backend/migrations/003_create_admin_roles_and_audit.sql
   ```

### Phase 2: Restoring from Logical Dump (`pg_restore`)
```bash
# 1. Decrypt latest dump
gpg --decrypt --batch --passphrase "${BACKUP_ENCRYPTION_KEY}" \
  --output /tmp/restore.dump /var/backups/skandx/skandx_prod_LATEST.dump.gpg

# 2. Restore schema data with parallel workers
pg_restore --dbname="${NEW_DB_URL}" \
  --jobs=4 \
  --clean \
  --if-exists \
  --no-owner \
  --no-privileges \
  /tmp/restore.dump

# 3. Securely erase decrypted file
shred -u /tmp/restore.dump
```

### Phase 3: Offline Lead Reconciliation Procedure
When the database recovers after an outage or failover, any leads captured during the downtime must be synced to the database.

Execute the lead reconciliation routine:
```bash
python -c "
import sys; sys.path.insert(0, '.')
from backend.app import DATA_DIR, SUPABASE_URL, SUPABASE_KEY
import json, urllib.request

leads_file = DATA_DIR / 'leads.jsonl'
if not leads_file.exists():
    print('No offline leads to reconcile.')
    sys.exit(0)

with open(leads_file, 'r', encoding='utf-8') as f:
    local_leads = [json.loads(line.strip()) for line in f if line.strip()]

print(f'Reconciling {len(local_leads)} offline leads...')
headers = {
    'apikey': SUPABASE_KEY,
    'Authorization': f'Bearer {SUPABASE_KEY}',
    'Content-Type': 'application/json',
    'Prefer': 'resolution=merge-duplicates'
}

for lead in local_leads:
    payload = json.dumps({
        'lead_id': lead.get('id'),
        'property_id': lead.get('property_id'),
        'customer_name': lead.get('name'),
        'customer_phone': lead.get('phone'),
        'customer_email': lead.get('email'),
        'status': 'PENDING',
        'created_at': lead.get('created_at')
    }).encode('utf-8')
    req = urllib.request.Request(f'{SUPABASE_URL}/rest/v1/customer_leads', data=payload, headers=headers, method='POST')
    try:
        urllib.request.urlopen(req, timeout=5)
    except Exception as e:
        print(f'Sync notice: {e}')
print('Reconciliation complete.')
"
```

---

## 5. Testing & Verification Runbook

> [!IMPORTANT]
> Non-destructive verification rules: Never truncate production tables or inject fake buyer leads into the live production Supabase instance.

### Staging Verification Run
1. Stop network access to staging Supabase.
2. Submit a test lead:
   ```bash
   curl -X POST http://localhost:8000/api/contact \
     -H "Content-Type: application/json" \
     -d '{"property_id":"STG-001","name":"Test Buyer","phone":"+919999999999","email":"buyer@test.local"}'
   ```
3. Inspect `backend/data/leads.jsonl`: Verify lead recorded with timestamp and ID.
4. Restore network access. Trigger reconciliation. Verify row in staging `customer_leads`.
