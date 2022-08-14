import click
import backup

@click.command()
@click.option('--now', is_flag=True, help="Whether to immediately run a backup then exit")
def run(now: bool):
    """Encrypted S3 backups for Postgres."""

    if now:
        backup.backup_databases()
    else:
        backup.run_schedule()

if __name__ == '__main__':
    run()