import os
from pathlib import Path

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError
from django.core.management.utils import get_random_secret_key

from config.credential_storage import (
    CREDENTIAL_STORAGE_ENV,
    CREDENTIAL_STORAGE_FILE,
    CREDENTIAL_STORAGE_SYSTEM,
    CredentialStorageError,
    is_placeholder_secret,
    set_system_credential,
)
from config.database import (
    DEFAULT_DATABASE_CIPHER_COMPATIBILITY,
    DEFAULT_DATABASE_CIPHER_PAGE_SIZE,
    DEFAULT_DATABASE_KDF_ITER,
    DEFAULT_DATABASE_NAME,
)
from config.env import parse_env_file
from config.file_backups import backup_existing_file
from config.recovery_kit import (
    RecoveryKitError,
    parse_recovery_kit,
    read_recovery_key,
    validate_database_key,
)


SECRET_KEY_NAME = "SECRET_KEY"
DATABASE_KEY_NAME = "DATABASE_ENCRYPTION_KEY"


def _quote_env_value(value):
    escaped_value = value.replace('"', '\\"')
    if any(char.isspace() for char in value) or "#" in value:
        return f'"{escaped_value}"'
    return value


class Command(BaseCommand):
    help = "Restore the local database key from a HolyFHIR Recovery Kit."

    def add_arguments(self, parser):
        source = parser.add_mutually_exclusive_group(required=True)
        source.add_argument(
            "--recovery-kit-file",
            help="Text file containing the HolyFHIR Recovery Kit.",
        )
        source.add_argument(
            "--recovery-key",
            help="Raw database recovery key copied from a HolyFHIR Recovery Kit.",
        )
        parser.add_argument(
            "--env-file",
            default=".env",
            help="Environment file to update. Default: .env.",
        )
        parser.add_argument(
            "--example-file",
            default=".env.example",
            help="Environment template used for supported setting keys. Default: .env.example.",
        )
        parser.add_argument(
            "--credential-storage",
            choices=(CREDENTIAL_STORAGE_SYSTEM, CREDENTIAL_STORAGE_FILE),
            default=os.getenv(CREDENTIAL_STORAGE_ENV, CREDENTIAL_STORAGE_SYSTEM),
            help=(
                "Where HolyFHIR should save the restored key. Use 'system' for this computer's secure storage "
                "or 'file' to store credentials in the settings file."
            ),
        )
        parser.add_argument(
            "--skip-database-check",
            action="store_true",
            help=(
                "Save the key without checking the current database file. "
                "Use only before restoring the database file."
            ),
        )

    def handle(self, *args, **options):
        base_dir = Path(settings.BASE_DIR)
        env_path = self._resolve_path(base_dir, options["env_file"])
        example_path = self._resolve_path(base_dir, options["example_file"])
        credential_storage = options["credential_storage"]

        database_key = self._read_database_key(options)
        example_values = parse_env_file(example_path) if example_path.exists() else {}
        env_values = parse_env_file(env_path) if env_path.exists() else {}
        values = {**example_values, **env_values}
        values[CREDENTIAL_STORAGE_ENV] = credential_storage

        database_path = self._database_path(base_dir, values)
        database_checked = self._check_database_key(
            database_path, database_key, values, skip=options["skip_database_check"]
        )

        self._store_restored_credentials(values, credential_storage, database_key)

        env_path.parent.mkdir(parents=True, exist_ok=True)
        backup_path = backup_existing_file(env_path)
        self._write_env_file(env_path, example_values, values)

        os.environ[CREDENTIAL_STORAGE_ENV] = credential_storage
        if credential_storage == CREDENTIAL_STORAGE_FILE:
            os.environ[DATABASE_KEY_NAME] = database_key
            os.environ[SECRET_KEY_NAME] = values[SECRET_KEY_NAME]

        if backup_path:
            self.stdout.write(
                self.style.WARNING(f"Backed up previous .env to {backup_path}")
            )
        if not database_checked:
            self.stdout.write(
                self.style.WARNING(
                    "No database file was checked. Restore the matching database backup before opening HolyFHIR."
                )
            )
        self.stdout.write(
            self.style.SUCCESS(
                "HolyFHIR saved the database key from your Recovery Kit."
            )
        )

    def _resolve_path(self, base_dir, path):
        resolved = Path(path)
        if resolved.is_absolute():
            return resolved
        return base_dir / resolved

    def _read_database_key(self, options):
        try:
            if options["recovery_kit_file"]:
                return read_recovery_key(options["recovery_kit_file"])
            return parse_recovery_kit(options["recovery_key"])
        except OSError as error:
            raise CommandError(f"Could not read Recovery Kit file: {error}") from error
        except RecoveryKitError as error:
            raise CommandError(str(error)) from error

    def _check_database_key(self, database_path, database_key, values, *, skip):
        if skip:
            return False

        if not database_path.exists():
            return False

        validate_database_key(
            database_path,
            database_key,
            cipher_page_size=self._int_value(
                values,
                "DATABASE_CIPHER_PAGE_SIZE",
                DEFAULT_DATABASE_CIPHER_PAGE_SIZE,
            ),
            kdf_iter=self._int_value(
                values, "DATABASE_KDF_ITER", DEFAULT_DATABASE_KDF_ITER
            ),
            cipher_compatibility=self._int_value(
                values,
                "DATABASE_CIPHER_COMPATIBILITY",
                DEFAULT_DATABASE_CIPHER_COMPATIBILITY,
            ),
        )
        return True

    def _store_restored_credentials(self, values, credential_storage, database_key):
        secret_key = values.get(SECRET_KEY_NAME, "")
        if is_placeholder_secret(SECRET_KEY_NAME, secret_key):
            secret_key = get_random_secret_key()

        if credential_storage == CREDENTIAL_STORAGE_SYSTEM:
            try:
                set_system_credential(DATABASE_KEY_NAME, database_key)
                set_system_credential(SECRET_KEY_NAME, secret_key)
            except CredentialStorageError as error:
                raise CommandError(str(error)) from error
            values[DATABASE_KEY_NAME] = ""
            values[SECRET_KEY_NAME] = ""
        else:
            values[DATABASE_KEY_NAME] = database_key
            values[SECRET_KEY_NAME] = secret_key

    def _database_path(self, base_dir, values):
        database_name = values.get("DATABASE_NAME") or str(
            base_dir / DEFAULT_DATABASE_NAME
        )
        database_path = Path(database_name)
        if database_path.is_absolute():
            return database_path
        return base_dir / database_path

    def _int_value(self, values, key, default):
        value = values.get(key)
        if value in {None, ""}:
            return default
        return int(value)

    def _write_env_file(self, env_path, example_values, values):
        lines = [
            "# Local HolyFHIR settings.",
            "# Updated from a HolyFHIR Recovery Kit. Do not commit this file.",
            "",
        ]

        keys = list(example_values) if example_values else sorted(values)
        for key in keys:
            lines.append(f"{key}={_quote_env_value(values.get(key, ''))}")

        extra_keys = sorted(set(values) - set(keys))
        if extra_keys:
            lines.extend(["", "# Additional local values"])
            for key in extra_keys:
                lines.append(f"{key}={_quote_env_value(values[key])}")

        env_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
