"""Snapshot the SQLite database into backups/ with a timestamp."""

import shutil
from datetime import datetime

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError


class Command(BaseCommand):
    help = "Copy the SQLite database to backups/db-<timestamp>.sqlite3."

    def add_arguments(self, parser):
        parser.add_argument("--keep", type=int, default=30, help="How many newest backups to keep.")

    def handle(self, *args, **options):
        source = str(settings.DATABASES["default"]["NAME"])
        backup_dir = settings.BASE_DIR / "backups"
        backup_dir.mkdir(exist_ok=True)
        stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
        dest = backup_dir / f"db-{stamp}.sqlite3"
        try:
            shutil.copy2(source, dest)
        except FileNotFoundError:
            raise CommandError(f"Database file not found: {source}")
        backups = sorted(backup_dir.glob("db-*.sqlite3"), reverse=True)
        for old in backups[options["keep"]:]:
            old.unlink()
        self.stdout.write(self.style.SUCCESS(f"Backed up to {dest}"))
