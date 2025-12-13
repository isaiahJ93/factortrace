# app/services/crypto_service.py
"""
Cryptographic services for report verification.

Provides:
- Ed25519 key generation
- Content hashing (SHA-256)
- Digital signatures
- QR code generation for verification URLs

Used by the verification layer to create tamper-evident, legally defensible
compliance reports with cryptographic proof.
"""
import hashlib
import io
import json
import logging
from dataclasses import dataclass
from datetime import datetime
from typing import Any, Dict, Optional, Tuple

import qrcode
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric.ed25519 import (
    Ed25519PrivateKey,
    Ed25519PublicKey,
)

from app.core.config import get_settings

logger = logging.getLogger(__name__)


@dataclass
class SignedReport:
    """Container for signed report data."""
    report_id: str
    content_hash: str
    signature: str
    signed_at: datetime
    verification_url: str
    public_key_hex: str


class CryptoService:
    """
    Cryptographic service for report signing and verification.

    Uses Ed25519 for digital signatures (fast, secure, compact).
    Keys are loaded from environment variables or can be generated.
    """

    def __init__(
        self,
        private_key_hex: Optional[str] = None,
        public_key_hex: Optional[str] = None,
        verification_url_base: Optional[str] = None,
    ):
        """
        Initialize crypto service with optional key material.

        Args:
            private_key_hex: Ed25519 private key as hex string (64 chars)
            public_key_hex: Ed25519 public key as hex string (64 chars)
            verification_url_base: Base URL for verification (e.g., https://factortrace.com/verify/)
        """
        settings = get_settings()

        self._private_key_hex = private_key_hex or settings.signing_private_key
        self._public_key_hex = public_key_hex or settings.signing_public_key
        self._verification_url_base = verification_url_base or settings.verification_url_base

        self._private_key: Optional[Ed25519PrivateKey] = None
        self._public_key: Optional[Ed25519PublicKey] = None

        # Load keys if provided
        if self._private_key_hex:
            self._load_private_key()
        if self._public_key_hex:
            self._load_public_key()

    def _load_private_key(self) -> None:
        """Load private key from hex string."""
        try:
            key_bytes = bytes.fromhex(self._private_key_hex)
            self._private_key = Ed25519PrivateKey.from_private_bytes(key_bytes)
            # Derive public key from private key
            self._public_key = self._private_key.public_key()
        except Exception as e:
            logger.error(f"Failed to load private key: {e}")
            raise ValueError("Invalid private key format")

    def _load_public_key(self) -> None:
        """Load public key from hex string."""
        try:
            key_bytes = bytes.fromhex(self._public_key_hex)
            self._public_key = Ed25519PublicKey.from_public_bytes(key_bytes)
        except Exception as e:
            logger.error(f"Failed to load public key: {e}")
            raise ValueError("Invalid public key format")

    @staticmethod
    def generate_key_pair() -> Tuple[str, str]:
        """
        Generate a new Ed25519 key pair.

        Returns:
            Tuple of (private_key_hex, public_key_hex)

        Usage:
            private_hex, public_hex = CryptoService.generate_key_pair()
            # Store private_hex in SIGNING_PRIVATE_KEY env var
            # Store public_hex in SIGNING_PUBLIC_KEY env var
        """
        private_key = Ed25519PrivateKey.generate()
        public_key = private_key.public_key()

        private_bytes = private_key.private_bytes(
            encoding=serialization.Encoding.Raw,
            format=serialization.PrivateFormat.Raw,
            encryption_algorithm=serialization.NoEncryption(),
        )

        public_bytes = public_key.public_bytes(
            encoding=serialization.Encoding.Raw,
            format=serialization.PublicFormat.Raw,
        )

        return private_bytes.hex(), public_bytes.hex()

    @staticmethod
    def hash_data(data: Any) -> str:
        """
        Compute SHA-256 hash of data.

        Args:
            data: Data to hash (dict, str, or bytes)

        Returns:
            Hex-encoded SHA-256 hash (64 chars)
        """
        if isinstance(data, dict):
            # Canonical JSON for deterministic hashing
            data_str = json.dumps(data, sort_keys=True, separators=(',', ':'))
            data_bytes = data_str.encode('utf-8')
        elif isinstance(data, str):
            data_bytes = data.encode('utf-8')
        elif isinstance(data, bytes):
            data_bytes = data
        else:
            data_bytes = str(data).encode('utf-8')

        return hashlib.sha256(data_bytes).hexdigest()

    def sign_data(self, data: bytes | str) -> str:
        """
        Sign data with Ed25519 private key.

        Args:
            data: Data to sign (bytes or string)

        Returns:
            Hex-encoded signature (128 chars)

        Raises:
            ValueError: If private key not configured
        """
        if not self._private_key:
            raise ValueError("Private key not configured")

        if isinstance(data, str):
            data = data.encode('utf-8')

        signature = self._private_key.sign(data)
        return signature.hex()

    def verify_signature(self, data: bytes | str, signature_hex: str) -> bool:
        """
        Verify Ed25519 signature.

        Args:
            data: Original data that was signed
            signature_hex: Hex-encoded signature

        Returns:
            True if signature is valid, False otherwise
        """
        if not self._public_key:
            raise ValueError("Public key not configured")

        if isinstance(data, str):
            data = data.encode('utf-8')

        try:
            signature = bytes.fromhex(signature_hex)
            self._public_key.verify(signature, data)
            return True
        except Exception:
            return False

    def sign_report(
        self,
        report_id: str,
        report_data: Dict[str, Any],
        tenant_id: Optional[str] = None,
    ) -> SignedReport:
        """
        Sign a complete report.

        Args:
            report_id: Unique report identifier
            report_data: Report content (emissions, company profile, etc.)
            tenant_id: Optional tenant ID for audit

        Returns:
            SignedReport with hash, signature, and verification URL
        """
        if not self._private_key:
            raise ValueError("Private key not configured - cannot sign report")

        signed_at = datetime.utcnow()

        # Compute content hash
        content_hash = self.hash_data(report_data)

        # Create signed payload (hash + report_id + timestamp)
        signed_payload = f"{content_hash}|{report_id}|{signed_at.isoformat()}"
        if tenant_id:
            signed_payload += f"|{tenant_id}"

        # Sign the payload
        signature = self.sign_data(signed_payload)

        # Build verification URL
        verification_url = f"{self._verification_url_base}{report_id}"

        # Get public key for verification
        public_bytes = self._public_key.public_bytes(
            encoding=serialization.Encoding.Raw,
            format=serialization.PublicFormat.Raw,
        )

        logger.info(f"Signed report {report_id} at {signed_at}")

        return SignedReport(
            report_id=report_id,
            content_hash=content_hash,
            signature=signature,
            signed_at=signed_at,
            verification_url=verification_url,
            public_key_hex=public_bytes.hex(),
        )

    def verify_report(
        self,
        report_id: str,
        report_data: Dict[str, Any],
        content_hash: str,
        signature: str,
        signed_at: datetime,
        tenant_id: Optional[str] = None,
    ) -> bool:
        """
        Verify a signed report.

        Args:
            report_id: Report identifier
            report_data: Report content
            content_hash: Stored content hash
            signature: Stored signature
            signed_at: When signature was created
            tenant_id: Optional tenant ID

        Returns:
            True if report is authentic and unmodified
        """
        # Verify content hash
        computed_hash = self.hash_data(report_data)
        if computed_hash != content_hash:
            logger.warning(f"Hash mismatch for report {report_id}")
            return False

        # Reconstruct signed payload
        signed_payload = f"{content_hash}|{report_id}|{signed_at.isoformat()}"
        if tenant_id:
            signed_payload += f"|{tenant_id}"

        # Verify signature
        is_valid = self.verify_signature(signed_payload, signature)

        if not is_valid:
            logger.warning(f"Signature verification failed for report {report_id}")

        return is_valid

    def get_public_key_hex(self) -> Optional[str]:
        """Get public key as hex string for offline verification."""
        if not self._public_key:
            return None

        public_bytes = self._public_key.public_bytes(
            encoding=serialization.Encoding.Raw,
            format=serialization.PublicFormat.Raw,
        )
        return public_bytes.hex()

    def is_configured(self) -> bool:
        """Check if signing keys are configured."""
        return self._private_key is not None


def generate_qr_code(
    url: str,
    size: int = 200,
    border: int = 2,
) -> bytes:
    """
    Generate a QR code image for a verification URL.

    Args:
        url: URL to encode in QR code
        size: Size in pixels (default 200)
        border: Border size in modules (default 2)

    Returns:
        PNG image bytes
    """
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_M,
        box_size=10,
        border=border,
    )
    qr.add_data(url)
    qr.make(fit=True)

    img = qr.make_image(fill_color="black", back_color="white")

    # Resize to requested size
    img = img.resize((size, size))

    # Convert to bytes
    buffer = io.BytesIO()
    img.save(buffer, format="PNG")
    buffer.seek(0)

    return buffer.getvalue()


def generate_verification_qr(report_id: str) -> bytes:
    """
    Generate QR code for report verification.

    Args:
        report_id: Report ID to encode

    Returns:
        PNG image bytes
    """
    settings = get_settings()
    verification_url = f"{settings.verification_url_base}{report_id}"
    return generate_qr_code(verification_url)


# Singleton service instance
_crypto_service: Optional[CryptoService] = None


def get_crypto_service() -> CryptoService:
    """Get singleton crypto service instance."""
    global _crypto_service
    if _crypto_service is None:
        _crypto_service = CryptoService()
    return _crypto_service


# =============================================================================
# EXPORTS
# =============================================================================

__all__ = [
    "CryptoService",
    "SignedReport",
    "generate_qr_code",
    "generate_verification_qr",
    "get_crypto_service",
]
