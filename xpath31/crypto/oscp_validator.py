# xpath31/crypto/ocsp_validator.py - OCSP validation with full EKU verification
"""OCSP response validation with proper authorization checks."""
import logging
from typing import Optional
from cryptography import x509
from cryptography.x509 import ocsp
from cryptography.x509.oid import ExtendedKeyUsageOID, ExtensionOID
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import rsa, ec, padding
import hashlib

logger = logging.getLogger(__name__)

class OCSPValidator:
    """Validates OCSP responses with full eIDAS compliance."""
    
    def verify_ocsp_response(self,
                           ocsp_resp: ocsp.OCSPResponse,
                           cert: x509.Certificate,
                           issuer_cert: x509.Certificate,
                           nonce: bytes) -> bool:
        """Verify OCSP response with full authorization checks.
        
        Args:
            ocsp_resp: Parsed OCSP response
            cert: Certificate being checked
            issuer_cert: Issuer of the certificate
            nonce: Expected nonce value
            
        Returns:
            True if response is valid and certificate is good
            
        Raises:
            ValueError: If validation fails
        """
        # Verify response status
        if ocsp_resp.response_status != ocsp.OCSPResponseStatus.SUCCESSFUL:
            raise ValueError(f"OCSP response status: {ocsp_resp.response_status}")
            
        # Verify nonce matches
        resp_nonce = self._extract_nonce(ocsp_resp)
        if resp_nonce != nonce:
            raise ValueError("OCSP nonce mismatch")
            
        # Find and verify responder certificate
        responder_cert = self._get_responder_cert(ocsp_resp, issuer_cert)
        
        # Verify responder authorization
        self._verify_responder_authorization(responder_cert, issuer_cert)
        
        # Verify response signature
        self._verify_response_signature(ocsp_resp, responder_cert)
        
        # Check certificate status
        cert_status = ocsp_resp.certificate_status
        if cert_status != ocsp.OCSPCertStatus.GOOD:
            raise ValueError(f"Certificate status: {cert_status}")
            
        logger.info("OCSP response fully verified")
        return True
        
    def _extract_nonce(self, ocsp_resp: ocsp.OCSPResponse) -> Optional[bytes]:
        """Extract nonce from OCSP response."""
        for ext in ocsp_resp.extensions:
            if isinstance(ext.value, x509.OCSPNonce):
                return ext.value.nonce
        return None
        
    def _get_responder_cert(self, 
                           ocsp_resp: ocsp.OCSPResponse,
                           issuer_cert: x509.Certificate) -> x509.Certificate:
        """Get and identify the OCSP responder certificate."""
        # Check if response is signed by issuer directly
        if ocsp_resp.responder_name:
            if ocsp_resp.responder_name == issuer_cert.subject:
                logger.info("OCSP response signed directly by issuer")
                return issuer_cert
                
        # Find responder cert in response
        responder_cert = None
        
        if ocsp_resp.responder_name:
            # Find by name
            for cert in ocsp_resp.certificates:
                if cert.subject == ocsp_resp.responder_name:
                    responder_cert = cert
                    break
        elif ocsp_resp.responder_key_hash:
            # Find by key hash
            for cert in ocsp_resp.certificates:
                key_bytes = cert.public_key().public_bytes(
                    encoding=serialization.Encoding.DER,
                    format=serialization.PublicFormat.SubjectPublicKeyInfo
                )
                key_hash = hashlib.sha1(key_bytes).digest()
                if key_hash == ocsp_resp.responder_key_hash:
                    responder_cert = cert
                    break
                    
        if not responder_cert:
            raise ValueError("OCSP responder certificate not found")
            
        return responder_cert
        
    def _verify_responder_authorization(self,
                                      responder_cert: x509.Certificate,
                                      issuer_cert: x509.Certificate):
        """Verify responder is authorized to sign OCSP responses."""
        # If responder is the issuer itself, it's authorized
        if self._certs_equal(responder_cert, issuer_cert):
            logger.info("OCSP responder is the certificate issuer")
            return
            
        # Otherwise, responder must have OCSP signing EKU
        try:
            eku_ext = responder_cert.extensions.get_extension_for_oid(
                ExtensionOID.EXTENDED_KEY_USAGE
            )
        except x509.ExtensionNotFound:
            raise ValueError("OCSP responder certificate lacks Extended Key Usage")
            
        if ExtendedKeyUsageOID.OCSP_SIGNING not in eku_ext.value:
            raise ValueError("OCSP responder certificate lacks OCSP signing EKU")
            
        # Verify responder cert is issued by the CA
        if responder_cert.issuer != issuer_cert.subject:
            raise ValueError("OCSP responder not issued by certificate's CA")
            
        # Verify signature
        try:
            issuer_cert.public_key().verify(
                responder_cert.signature,
                responder_cert.tbs_certificate_bytes,
                padding.PKCS1v15(),
                responder_cert.signature_hash_algorithm
            )
        except Exception as e:
            raise ValueError(f"OCSP responder certificate signature invalid: {e}")
            
        logger.info("OCSP responder authorization verified (delegated signing)")
        
    def _verify_response_signature(self,
                                 ocsp_resp: ocsp.OCSPResponse,
                                 responder_cert: x509.Certificate):
        """Verify OCSP response signature."""
        public_key = responder_cert.public_key()
        signature_algorithm = ocsp_resp.signature_algorithm_oid._name
        
        if isinstance(public_key, rsa.RSAPublicKey):
            if 'pss' in signature_algorithm.lower():
                padding_algo = padding.PSS(
                    mgf=padding.MGF1(hashes.SHA256()),
                    salt_length=padding.PSS.MAX_LENGTH
                )
            else:
                padding_algo = padding.PKCS1v15()
                
            public_key.verify(
                ocsp_resp.signature,
                ocsp_resp.tbs_response_bytes,
                padding_algo,
                ocsp_resp.signature_hash_algorithm
            )
        elif isinstance(public_key, ec.EllipticCurvePublicKey):
            public_key.verify(
                ocsp_resp.signature,
                ocsp_resp.tbs_response_bytes,
                ec.ECDSA(ocsp_resp.signature_hash_algorithm)
            )
        else:
            raise ValueError(f"Unsupported public key type: {type(public_key)}")
            
        logger.debug("OCSP response signature verified")
        
    def _certs_equal(self, cert1: x509.Certificate, cert2: x509.Certificate) -> bool:
        """Compare two certificates for equality."""
        return (cert1.public_bytes(serialization.Encoding.DER) == 
                cert2.public_bytes(serialization.Encoding.DER))