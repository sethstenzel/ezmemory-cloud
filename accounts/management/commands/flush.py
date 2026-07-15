"""Guarded replacement for Django's flush command.

The default database holds real user data. Flushing it must be a deliberate,
explicit act: set EZMEMORY_ALLOW_FLUSH=1 in the environment to proceed.
"""

import os

from django.core.management.base import CommandError
from django.core.management.commands.flush import Command as FlushCommand


class Command(FlushCommand):
    def handle(self, **options):
        if os.environ.get("EZMEMORY_ALLOW_FLUSH") != "1":
            raise CommandError(
                "Refusing to flush: this database contains real user data. "
                "Set EZMEMORY_ALLOW_FLUSH=1 (and preferably EZMEMORY_DB_PATH to a "
                "throwaway copy) if you really mean it. Run `manage.py backupdb` first."
            )
        return super().handle(**options)
