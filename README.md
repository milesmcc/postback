# Postback

Postback provides encrypted S3 backups for Postgres. Better documentation coming, maybe.

## Environment Variables

* `AWS_ACCESS_KEY_ID` — your AWS access key ID (for s3)
* `AWS_SECRET_ACCESS_KEY` — your AWS secret access key (for s3)
* `PG_URL` — a complete Postgres connection URL (database does not matter)
* `SKIP_DATABASES` — comma-separated list of databases to skip (default: `postgres`; e.g., `postgres,temp_database,etc`)
* `AGE_RECIPIENTS` — comma-separated list of [age](https://age-encryption.org) public keys
* `S3_BUCKET` — S3 bucket to upload backups to
* `OBJECT_PREFIX` — prefix to apply to backup object names
* `CRON_SCHEDULE` — the schedule for backups (in crontab format)


