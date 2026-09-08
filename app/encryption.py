from cryptography.fernet import Fernet

from app.config import settings


def _get_fernet():

    key = settings.DB_ENCRYPTION_KEY

    if not key:
        raise RuntimeError(
            "DB_ENCRYPTION_KEY is missing from the .env file."
        )

    try:

        return Fernet(
            key.encode()
        )

    except Exception as exc:

        raise RuntimeError(
            "DB_ENCRYPTION_KEY is invalid. "
            "Generate a valid Fernet key."
        ) from exc


def encrypt_password(password: str) -> str:

    if not password:
        return ""

    return (
        _get_fernet()
        .encrypt(password.encode())
        .decode()
    )


def decrypt_password(encrypted_password: str) -> str:

    if not encrypted_password:
        return ""

    return (
        _get_fernet()
        .decrypt(encrypted_password.encode())
        .decode()
    )