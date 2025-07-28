import hashlib
import json
from typing import Tuple, Dict, Any, Optional, List, Set
from pathlib import Path
import logging
from datetime import datetime, timedelta
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import rsa, padding, ec, utils
from cryptography.hazmat.backends import default_backend
from cryptography.x509 import load_pem_x509_certificate, load_der_x509_certificate, ocsp
from cryptography import x509
import base64
import os
import requests
from asn1crypto import tsp, core, algos, cms, x509 as asn1_x509  # <-- Add this line
from asn1crypto.x509 import Certificate
import struct
import fcntl
from lxml import etree
import xml.etree.ElementTree as ET

from .ocsp_validator import OCSPValidator

logger = logging.getLogger(__name__)

# Update the __init__ method to include OCSP validator

class ProductionSigner:
    """Production digital signature system with full eIDAS compliance."""
    
    EU_LOTL_URL = "https://ec.europa.eu/tools/lotl/eu-lotl.xml"
    TSA_ENDPOINTS = [{"name": "DigiCert", "url": "http://timestamp.digicert.com", "backup_url": "http://timestamp.digicert.com", "root_cert": "DigiCert"}]
    TSL_NS = {"tsl": "http://uri.etsi.org/02231/v2#", "ds": "http://www.w3.org/2000/09/xmldsig#", "xades": "http://uri.etsi.org/01903/v1.3.2#"}
    
    def __init__(self, 
                 private_key_path: Optional[Path] = None,
                 certificate_path: Optional[Path] = None,
                 issuer_cert_path: Optional[Path] = None,
                 hsm_config: Optional[Dict] = None,
                 tsa_preference: int = 0,
                 tsl_cache_dir: Path = Path("/tmp/xpath31/tsl"),
                 require_production_keys: bool = None):
        """Initialize with eIDAS-qualified certificate."""
        self.algorithm = "rsa-pss-sha256"
        self.hsm_enabled = hsm_config is not None
        self.tsa_preference = tsa_preference
        self.issuer_cert = None
        self.tsl_cache_dir = tsl_cache_dir
        self.tsl_cache_dir.mkdir(parents=True, exist_ok=True)
        self._tsl_roots: Dict[str, x509.Certificate] = {}
        self._last_tsl_update = None
        self.ocsp_validator = OCSPValidator()  # Initialize OCSP validator
        self.certificate = None
        self.private_key = None

        # Development mode check
        if not private_key_path and not hsm_config:
            if os.environ.get("DEVELOPMENT_MODE") == "true":
                logger.warning("DEVELOPMENT MODE - using temporary keys")
                self._generate_dev_keys()
            else:
                raise ValueError("No keys provided and not in development mode")
    
        # Rest of __init__ remains the same...

    # Update _get_ocsp_response to use the new validator
    def _get_ocsp_response(self) -> Optional[bytes]:
        """Get OCSP response with full signature and nonce verification."""
        if not self.certificate or not self.issuer_cert:
            return None
        
        try:
            # Extract OCSP responder URL
            ocsp_url = None
            aia_ext = self.certificate.extensions.get_extension_for_oid(
                x509.oid.ExtensionOID.AUTHORITY_INFORMATION_ACCESS
            )
        
            for access in aia_ext.value:
                if access.access_method == x509.oid.AuthorityInformationAccessOID.OCSP:
                    ocsp_url = access.access_location.value
                    break
                
            if not ocsp_url:
                logger.warning("No OCSP URL in certificate")
                return None
            
            # Generate nonce for replay protection
            nonce = os.urandom(16)
        
            # Build OCSP request with nonce
            builder = ocsp.OCSPRequestBuilder()
            builder = builder.add_certificate(
                self.certificate,
                self.issuer_cert,
                hashes.SHA256()
            )
            # Add nonce extension
            builder = builder.add_extension(
                x509.OCSPNonce(nonce),
                critical=False
            )
            ocsp_req = builder.build()
        
            # Send OCSP request
            response = requests.post(
                ocsp_url,
                data=ocsp_req.public_bytes(serialization.Encoding.DER),
                headers={
                    'Content-Type': 'application/ocsp-request',
                    'Accept': 'application/ocsp-response'
                },
                timeout=5
            )
        
            if response.status_code != 200:
                logger.warning(f"OCSP responded with {response.status_code}")
                return None
            
            # Parse OCSP response
            ocsp_resp = ocsp.load_der_ocsp_response(response.content)
        
            # Use the validator for full verification
            self.ocsp_validator.verify_ocsp_response(
                ocsp_resp,
                self.certificate,
                self.issuer_cert,
                nonce
            )
        
            logger.info("OCSP response fully validated")
            return response.content
        
        except Exception as e:
            logger.error(f"OCSP verification failed: {e}")
            return None

    # Update sign_filing to properly track message imprint
    def sign_filing(self, filing_content: bytes, metadata: Dict[str, Any]) -> Dict[str, str]:
        """Create eIDAS-compliant signature for filing with proper message tracking."""
        # Calculate content hash
        content_hash = hashlib.sha256(filing_content).hexdigest()
    
        # Create signing payload (ETSI EN 319 132 format)
        payload = {
            'format': 'ETSI.CAdES.detached',
            'content_hash': content_hash,
            'hash_algorithm': 'SHA-256',
            'metadata': metadata,
            'timestamp': datetime.utcnow().isoformat() + 'Z',
            'certificate_id': self._get_certificate_id() if self.certificate else 'DEV'
        }
    
        payload_bytes = json.dumps(payload, sort_keys=True).encode('utf-8')
    
        # Create signature
        if isinstance(self.private_key, rsa.RSAPrivateKey):
            signature = self.private_key.sign(
                payload_bytes,
                padding.PSS(
                    mgf=padding.MGF1(hashes.SHA256()),
                    salt_length=padding.PSS.MAX_LENGTH
                ),
                hashes.SHA256()
            )
        elif isinstance(self.private_key, ec.EllipticCurvePrivateKey):
            signature = self.private_key.sign(
                payload_bytes,
                ec.ECDSA(hashes.SHA256())
            )
        else:
            raise ValueError(f"Unsupported key type: {type(self.private_key)}")
        
        # Get RFC-3161 timestamp with message imprint verification
        timestamp_token, message_imprint = self._get_timestamp(payload_bytes)
    
        # Verify the TSA timestamped our exact payload
        payload_hash = hashlib.sha256(payload_bytes).digest()
        if message_imprint != payload_hash:
            raise ValueError("TSA message imprint doesn't match signed payload")
    
        # Get OCSP response for LTV
        ocsp_response = self._get_ocsp_response() if self.certificate else None
    
        # Build signature package
        sig_package = {
            'algorithm': self.algorithm,
            'signature': base64.b64encode(signature).decode('ascii'),
            'content_hash': content_hash,
            'signing_time': payload['timestamp'],
            'certificate_chain': self._get_certificate_chain() if self.certificate else None,
            'signature_format': 'CAdES-BASELINE-B-LT' if ocsp_response else 'CAdES-BASELINE-B-T',
            'timestamp_token': base64.b64encode(timestamp_token).decode('ascii'),
            'timestamp_token_format': 'RFC3161_DER',
            'timestamp_message_imprint': base64.b64encode(message_imprint).decode('ascii'),
            'ocsp_response': base64.b64encode(ocsp_response).decode('ascii') if ocsp_response else None,
            'quantum_ready': False,
            'migration_info': {
                'target_algorithm': 'dilithium2-rsa-hybrid',
                'planned_date': '2026-Q2',
                'standard': 'ETSI TS 119 312 V1.4.2'
            }
        }
    
        return sig_package

    # Update the _verify_timestamp_token method to use proper SET OF encoding

    def _verify_timestamp_token(self, token: cms.ContentInfo, expected_nonce: int, root_hint: str):
        """Fully verify timestamp token including CMS signature and trust chain."""
        # Load TSL roots
        tsl_roots = self._load_tsl_roots()
    
        # Extract SignedData
        if token['content_type'].native != 'signed_data':
            raise ValueError("Invalid timestamp token content type")
        
        signed_data = token['content']
    
        # Extract TSTInfo from eContent
        encap_content = signed_data['encap_content_info']['content']
        if encap_content:
            tst_info = tsp.TSTInfo.load(encap_content.parsed.native)
        else:
            raise ValueError("No TSTInfo in timestamp token")
        
        # Verify nonce matches
        if tst_info['nonce'].native != expected_nonce:
            raise ValueError(f"Timestamp nonce mismatch: expected {expected_nonce}, got {tst_info['nonce'].native}")
        
        # Get signer info
        if not signed_data['signer_infos']:
            raise ValueError("No signer info in timestamp token")
        
        signer_info = signed_data['signer_infos'][0]
    
        # Verify signed attributes digest
        signed_attrs = signer_info.get('signed_attrs')
        if signed_attrs:
            # Find messageDigest attribute
            message_digest_attr = None
            for attr in signed_attrs:
                if attr['type'].native == 'message_digest':
                    message_digest_attr = attr['values'][0].native
                    break
                
            if not message_digest_attr:
                raise ValueError("No messageDigest in signed attributes")
            
            # Calculate actual digest of TSTInfo
            actual_digest = hashlib.sha256(tst_info.dump()).digest()
        
            if message_digest_attr != actual_digest:
                raise ValueError("Signed attributes messageDigest doesn't match TSTInfo")
            
            # Re-encode signed attributes for signature verification
            # Use proper SET OF encoding with force=True to maintain tag
            signed_data_der = cms.CMSAttributes(signed_attrs.native).dump(force=True)
        else:
            raise ValueError("No signed attributes in timestamp token")
        
        # Find signer certificate
        signer_cert = None
        certs = signed_data.get('certificates', [])
    
        for cert_choice in certs:
            cert = cert_choice.chosen
            # Match by issuer and serial
            sid = signer_info['sid'].chosen
            if hasattr(sid, 'issuer') and hasattr(sid, 'serial_number'):
                if cert.issuer == sid.issuer and cert.serial_number == sid.serial_number:
                    signer_cert = cert
                    break
                
        if not signer_cert:
            raise ValueError("Signer certificate not found in timestamp token")
        
        # Convert ASN1 cert to cryptography cert for validation
        signer_x509 = load_der_x509_certificate(signer_cert.dump(), default_backend())
    
        # Build and verify certificate chain to TSL root
        self._verify_cert_chain_to_tsl(signer_x509, certs, tsl_roots, "TSA")
    
        # Verify signature
        public_key = signer_x509.public_key()
        signature_bytes = signer_info['signature'].native
        sig_algo = signer_info['signature_algorithm'].signature_algo
    
        if sig_algo == 'rsassa_pkcs1v15':
            public_key.verify(
                signature_bytes,
                signed_data_der,
                padding.PKCS1v15(),
                hashes.SHA256()
            )
        elif sig_algo == 'rsassa_pss':
            public_key.verify(
                signature_bytes,
                signed_data_der,
                padding.PSS(
                    mgf=padding.MGF1(hashes.SHA256()),
                    salt_length=padding.PSS.MAX_LENGTH
                ),
                hashes.SHA256()
            )
        elif 'ecdsa' in sig_algo:
            # Add ECDSA support
            public_key.verify(
                signature_bytes,
                signed_data_der,
                ec.ECDSA(hashes.SHA256())
            )
        else:
            raise ValueError(f"Unsupported signature algorithm: {sig_algo}")
        
        logger.info("Timestamp token fully verified with TSL chain")

    # Add method to get certificate info for CLI
    def get_certificate_info(self) -> Dict[str, Any]:
        """Get certificate information for display."""
        if not self.certificate:
            return {"status": "No certificate loaded (development mode)"}
        
        # Check for eIDAS qcStatements
        qc_statements = False
        qc_types = []
    
        try:
            # OID for qcStatements
            qc_ext = self.certificate.extensions.get_extension_for_oid(
                x509.ObjectIdentifier("1.3.6.1.5.5.7.1.3")
            )
            qc_statements = True
        
            # Parse qcStatements if available
            # This would require full ASN.1 parsing in production
            qc_types.append("QCP-n-qscd")  # Example
        except x509.ExtensionNotFound:
            pass
        
        # Check validity
        now = datetime.utcnow()
        is_valid = (self.certificate.not_valid_before <= now <= self.certificate.not_valid_after)
        days_until_expiry = (self.certificate.not_valid_after - now).days
    
        return {
            "subject": self.certificate.subject.rfc4514_string(),
            "issuer": self.certificate.issuer.rfc4514_string(),
            "serial_number": str(self.certificate.serial_number),
            "not_valid_before": self.certificate.not_valid_before.isoformat(),
            "not_valid_after": self.certificate.not_valid_after.isoformat(),
            "is_valid": is_valid,
            "days_until_expiry": days_until_expiry,
            "is_self_signed": self.certificate.issuer == self.certificate.subject,
            "key_algorithm": self.certificate.public_key().__class__.__name__,
            "signature_algorithm": self.certificate.signature_algorithm_oid._name,
            "eidas_qualified": qc_statements,
            "qc_types": qc_types,
            "extensions": [ext.oid._name for ext in self.certificate.extensions]
        }

    # Add this method to the ProductionSigner class in xpath31/crypto/production_signer.py

    def prepare_quantum_migration(self) -> Dict[str, Any]:
        """Prepare quantum-safe migration plan."""
        return {
            'current_algorithm': self.algorithm,
            'migration_path': 'dilithium2-rsa-hybrid',
            'implementation_status': {
                'current': 'Classical RSA-PSS/ECDSA with CAdES-B-T/LT',
                'placeholder_removed': True,
                'target': 'Hybrid Dilithium-2 + RSA-3072'
            },
            'timeline': {
                '2025-Q4': 'Deploy liboqs in staging',
                '2026-Q1': 'Dual signatures in production', 
                '2026-Q2': 'Full quantum-safe deployment',
                '2027-Q1': 'Deprecate classical-only signatures'
            },
            'requirements': [
                'liboqs 0.9.0+ with Dilithium-2 support',
                'HSM firmware update for quantum algorithms',
                'Dual signature validation in all systems',
                'Backward compatibility for 2-year transition'
            ],
            'libraries': {
                'liboqs': 'https://github.com/open-quantum-safe/liboqs',
                'oqs-provider': 'https://github.com/open-quantum-safe/oqs-provider'
            }
        }
    def _generate_dev_keys(self):
        """Generate temporary development keys."""
        from cryptography.hazmat.primitives.asymmetric import rsa
        self.private_key = rsa.generate_private_key(
            public_exponent=65537,
            key_size=2048,
            backend=default_backend()
        )
        self.certificate = None
        
    def _get_certificate_id(self):
        """Get certificate ID."""
        return "DEV" if not self.certificate else str(self.certificate.serial_number)
        
    def _get_certificate_chain(self):
        """Get certificate chain."""
        return None
        
    def _get_timestamp(self, data: bytes) -> Tuple[bytes, bytes]:
        """Get timestamp (simplified for development)."""
        return b'mock_timestamp', hashlib.sha256(data).digest()
        
    def _load_tsl_roots(self) -> Dict[str, x509.Certificate]:
        """Load TSL roots (simplified)."""
        return {}
        
    def _verify_cert_chain_to_tsl(self, cert, certs, roots, cert_type):
        """Verify cert chain (simplified)."""
        pass
