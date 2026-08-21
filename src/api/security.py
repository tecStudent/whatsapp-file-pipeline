import hashlib
import hmac

SIGNATURE_PREFIX = "sha256="


def is_valid_meta_signature(payload: bytes, signature: str | None, app_secret: str) -> bool:
    """Validate a Meta X-Hub-Signature-256 header against the raw request body."""

    if not signature or not app_secret or not signature.startswith(SIGNATURE_PREFIX):
        return False

    supplied_digest = signature.removeprefix(SIGNATURE_PREFIX)
    expected_digest = hmac.new(
        app_secret.encode("utf-8"),
        payload,
        hashlib.sha256,
    ).hexdigest()

    return hmac.compare_digest(supplied_digest, expected_digest)

