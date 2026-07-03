from datetime import datetime, timezone
from pathlib import Path

from django.core.exceptions import ImproperlyConfigured

from config.database import (
    DEFAULT_DATABASE_CIPHER_COMPATIBILITY,
    DEFAULT_DATABASE_CIPHER_PAGE_SIZE,
    DEFAULT_DATABASE_KDF_ITER,
)
from config.sqlcipher import get_sqlcipher_dbapi


RECOVERY_KIT_VERSION = "1"
RECOVERY_KIT_TITLE = "HolyFHIR Recovery Kit"


class RecoveryKitError(ValueError):
    pass


def render_recovery_kit(database_key, created_at=None):
    created_at = created_at or datetime.now(timezone.utc)
    created_at_text = created_at.astimezone(timezone.utc).strftime(
        "%Y-%m-%d %H:%M:%S UTC"
    )

    return "\n".join(
        [
            RECOVERY_KIT_TITLE,
            f"Version: {RECOVERY_KIT_VERSION}",
            f"Created: {created_at_text}",
            "",
            "Save this somewhere safe.",
            "You may need this if you move HolyFHIR to another computer or restore a backup.",
            "",
            f"Database Recovery Key: {database_key}",
            "",
            "Keep this Recovery Kit separate from your computer backups when possible.",
            "Anyone with this key and your database backup may be able to open your local records.",
            "",
        ]
    )


def parse_recovery_kit(text):
    value = (text or "").strip()
    if not value:
        raise RecoveryKitError("Recovery Kit is empty.")

    for raw_line in value.splitlines():
        line = raw_line.strip()
        if line.lower().startswith("database recovery key:"):
            key = line.split(":", 1)[1].strip()
            if key:
                return key

    if "\n" not in value and ":" not in value:
        return value

    raise RecoveryKitError("Recovery Kit does not include a database recovery key.")


def read_recovery_key(path):
    return parse_recovery_kit(Path(path).read_text(encoding="utf-8"))


def _sql_quote(value):
    return str(value).replace("'", "''")


def validate_database_key(
    database_name,
    database_key,
    *,
    cipher_page_size=DEFAULT_DATABASE_CIPHER_PAGE_SIZE,
    kdf_iter=DEFAULT_DATABASE_KDF_ITER,
    cipher_compatibility=DEFAULT_DATABASE_CIPHER_COMPATIBILITY,
):
    database_path = Path(database_name)
    if not database_path.exists():
        return False

    database = get_sqlcipher_dbapi()
    connection = database.connect(str(database_path))
    try:
        connection.execute(f"PRAGMA key = '{_sql_quote(database_key)}'")
        if cipher_compatibility:
            connection.execute(
                f"PRAGMA cipher_compatibility = {int(cipher_compatibility)}"
            )
        if cipher_page_size:
            connection.execute(f"PRAGMA cipher_page_size = {int(cipher_page_size)}")
        if kdf_iter:
            connection.execute(f"PRAGMA kdf_iter = {int(kdf_iter)}")
        connection.execute("SELECT count(*) FROM sqlite_master")
    except database.DatabaseError as error:
        raise ImproperlyConfigured(
            "HolyFHIR could not open the encrypted database with this Recovery Kit."
        ) from error
    finally:
        connection.close()

    return True
