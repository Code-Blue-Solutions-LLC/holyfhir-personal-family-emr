from pathlib import Path

from django.core.management.base import BaseCommand, CommandError

from config.credential_storage import CredentialStorageError, get_configured_secret
from config.recovery_kit import render_recovery_kit


class Command(BaseCommand):
    help = "Export a HolyFHIR Recovery Kit for the local encrypted database."

    def add_arguments(self, parser):
        parser.add_argument(
            "--output",
            required=True,
            help="Path where the Recovery Kit text file should be saved.",
        )

    def handle(self, *args, **options):
        try:
            database_key = get_configured_secret("DATABASE_ENCRYPTION_KEY")
        except CredentialStorageError as error:
            raise CommandError(str(error)) from error

        if not database_key:
            raise CommandError(
                "HolyFHIR could not find the database key to export a Recovery Kit."
            )

        output_path = Path(options["output"])
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(render_recovery_kit(database_key), encoding="utf-8")

        self.stdout.write(
            self.style.SUCCESS(f"Saved HolyFHIR Recovery Kit to {output_path}")
        )
