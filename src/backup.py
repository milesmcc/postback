import base64
from datetime import date, datetime
import itertools
from pathlib import Path
import subprocess
import os
from time import sleep, time
import psycopg
from typing import Iterable, Optional
from croniter import croniter
import traceback
import tempfile
from loguru import logger
import boto3

# Note: We use tempfile.mktemp(). Yeah. It has to be this way, since we're intentionally passing the paths to subprocesses.


def get_connection_string(database: Optional[str] = None) -> str:
    base = os.getenv("PG_URL")
    if database is not None:
        return base[: base.rfind("/")] + "/" + database
    return base


def list_databases() -> Iterable[str]:
    to_skip = os.getenv("SKIP_DATABASES", "postgres").split(",")

    with psycopg.connect(get_connection_string()) as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT datname FROM pg_database WHERE datistemplate = false;")

            for (record,) in cur:
                if record not in to_skip:
                    yield record


def export_database(database: str) -> str:
    logger.info(f"Exporting database `{database}`...")
    output_path = tempfile.mktemp(prefix="pg_dump", suffix="database")
    subprocess.run(
        ["pg_dump", "-d", get_connection_string(database), "-f", output_path]
    ).check_returncode()
    return output_path


def compress_file(path: str) -> str:
    logger.info(f"Compressing {path}...")
    compressed_output_path = tempfile.mktemp(prefix="compressed", suffix="database")
    subprocess.run(["zstd", path, "-o", compressed_output_path]).check_returncode()
    return compressed_output_path


def get_age_recipients() -> Iterable[str]:
    return os.getenv("AGE_RECIPIENTS").split(",")


def encrypt_file(path: str) -> str:
    logger.info(f"Encrypting {path}...")
    encrypted_output_path = tempfile.mktemp(prefix="encrypted", suffix="database")
    subprocess.run(
        ["age", "--encrypt", "-o", encrypted_output_path]
        + list(
            itertools.chain(*(["-r", recipient] for recipient in get_age_recipients()))
        )
        + [path]
    ).check_returncode()
    return encrypted_output_path


def get_checksum(path: str) -> str:
    logger.info(f"Calculating checksum of {path}...")
    checksum_output = subprocess.run(["sha256sum", path], capture_output=True)
    checksum_output.check_returncode()
    return checksum_output.stdout.decode().split()[0]


def upload_to_s3(
    file_name: str, database_name: str, timestamp: datetime, checksum: str
):
    """Upload a file to an S3 bucket."""

    bucket = os.getenv("S3_BUCKET")

    # Determine object name
    object_prefix = os.getenv("OBJECT_PREFIX", "backup")
    object_name = f"{timestamp.year}/{timestamp.month:02d}/{object_prefix}_{timestamp.isoformat()}_{database_name}_{checksum}.sql.zst.age"

    # Log it!
    logger.info(f"Uploading backup to S3: {object_name}")

    # Upload the file
    s3_client = boto3.client("s3")
    s3_client.upload_file(
        file_name,
        bucket,
        object_name,
        ExtraArgs={
            "Metadata": {"database": database_name},
            "ChecksumAlgorithm": "SHA256",
        },
    )

    # Verify file integrity
    head = s3_client.head_object(Bucket=bucket, Key=object_name, ChecksumMode="ENABLED")
    amz_checksum = base64.decodebytes(
        head["ResponseMetadata"]["HTTPHeaders"]["x-amz-checksum-sha256"].encode()
    ).hex()  # Amazon base64 encodes the data
    if amz_checksum != checksum:
        logger.error(f"Checksum did not match for {database_name} backup!")
        raise ValueError("Upload checksum did not match!")
    else:
        logger.info(f"Checksum matched for {database_name} backup!")


def backup_database(database: str) -> bool:
    """Compresses, encrypts, and hashes the database dump at the given path."""

    logger.info(f"Backing up {database}...")

    # Step 0: export
    dump_path = export_database(database)

    # Step 1: compress
    compressed_output_path = compress_file(dump_path)
    os.remove(dump_path)

    # Step 2: encrypt
    encrypted_output_path = encrypt_file(compressed_output_path)
    os.remove(compressed_output_path)

    # Step 3: hash
    checksum = get_checksum(encrypted_output_path)

    # Step 4: upload to S3
    upload_to_s3(encrypted_output_path, database, datetime.now(), checksum)

    # Step 5: cleanup
    os.remove(encrypted_output_path)

def backup_databases():
    logger.info("Backing up databases...")

    for database in list_databases():
        backup_database(database)

def run_schedule():
    logger.info("Running crontab schedule...")
    while True:
        try:
            next_runtime = croniter(os.getenv("CRON_SCHEDULE", "0 * * * *"), datetime.now()).get_next(datetime)
            
            while datetime.now() < next_runtime:
                seconds = (next_runtime - datetime.now()).total_seconds()
                logger.info(f"Next run in {seconds} seconds. Sleeping...")
                sleep(seconds)
            
            backup_databases()
        except Exception as e:
            logger.error(f"Encountered an error while backing up the databases: {e}")
            traceback.print_exc()

if __name__ == "__main__":
    print(backup_databases)
