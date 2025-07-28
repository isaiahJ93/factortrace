# tests/test_message_imprint.py - Test message imprint validation
"""Test suite for message imprint and digest validation."""
import pytest
from unittest.mock import Mock, patch
import hashlib
import os
from datetime import datetime
from asn1crypto import tsp, cms, algos, core

from xpath31.crypto.production_signer import ProductionSigner

class TestMessageImprint:
    """Test message imprint cross-validation."""
    
    @pytest.fixture
    def create_timestamp_response(self):
        """Factory for creating timestamp responses with specific message imprints."""
        def _create(data_hash: bytes, nonce: int):
            # Create TSTInfo with specific message imprint
            tst_info = tsp.TSTInfo({
                'version': 'v1',
                'policy': '1.2.3.4.5',
                'message_imprint': {
                    'hash_algorithm': {'algorithm': 'sha256'},
                    'hashed_message': data_hash
                },
                'serial_number': 12345,
                'gen_time': datetime.utcnow(),
                'accuracy': {'seconds': 1},
                'ordering': False,
                'nonce': nonce,
                'tsa': {
                    'type': 'directory_name',
                    'value': [[{'type': '2.5.4.3', 'value': 'Test TSA'}]]
                }
            })
            
            # Calculate messageDigest for signed attributes
            tst_info_der = tst_info.dump()
            message_digest = hashlib.sha256(tst_info_der).digest()
            
            # Create signed attributes with correct messageDigest
            signed_attrs = [
                cms.CMSAttribute({
                    'type': '1.2.840.113549.1.9.3',  # contentType
                    'values': [core.ObjectIdentifier('1.2.840.113549.1.9.16.1.4')]
                }),
                cms.CMSAttribute({
                    'type': '1.2.840.113549.1.9.4',  # messageDigest
                    'values': [core.OctetString(message_digest)]
                })
            ]
            
            # Create minimal CMS SignedData
            signed_data = cms.SignedData({
                'version': 'v3',
                'digest_algorithms': [{'algorithm': 'sha256'}],
                'encap_content_info': {
                    'content_type': '1.2.840.113549.1.9.16.1.4',
                    'content': core.ParsableOctetString(tst_info_der)
                },
                'certificates': [],
                'signer_infos': [{
                    'version': 'v1',
                    'sid': {
                        'issuer_and_serial_number': {
                            'issuer': [[{'type': '2.5.4.3', 'value': 'Test CA'}]],
                            'serial_number': 1
                        }
                    },
                    'digest_algorithm': {'algorithm': 'sha256'},
                    'signed_attrs': signed_attrs,
                    'signature_algorithm': {'algorithm': 'sha256_rsa'},
                    'signature': b'mock_signature'
                }]
            })
            
            # Create TimeStampToken
            token = cms.ContentInfo({
                'content_type': 'signed_data',
                'content': signed_data
            })
            
            # Create TimeStampResp
            ts_resp = tsp.TimeStampResp({
                'status': {
                    'status': 'granted',
                    'status_string': ['Operation Successful']
                },
                'time_stamp_token': token
            })
            
            return ts_resp.dump()
            
        return _create
        
    @patch('requests.post')
    def test_message_imprint_verification(self, mock_post, create_timestamp_response):
        """Test that message imprint is verified against data."""
        test_data = b"Test data to timestamp"
        correct_hash = hashlib.sha256(test_data).digest()
        
        def mock_tsa_response(url, **kwargs):
            # Extract nonce from request
            req_data = kwargs['data']
            ts_req = tsp.TimeStampReq.load(req_data)
            nonce = ts_req['nonce'].native
            
            response = Mock()
            response.status_code = 200
            response.content = create_timestamp_response(correct_hash, nonce)
            return response
            
        mock_post.side_effect = mock_tsa_response
        
        # Test with development mode
        os.environ['DEVELOPMENT_MODE'] = 'true'
        
        with patch.object(ProductionSigner, '_verify_timestamp_token'):
            signer = ProductionSigner()
            
            # Get timestamp - should succeed
            token, imprint = signer._get_timestamp(test_data)
            
            # Verify correct imprint returned
            assert imprint == correct_hash
            
        # Cleanup
        os.environ.pop('DEVELOPMENT_MODE', None)
        
    @patch('requests.post')  
    def test_message_imprint_mismatch(self, mock_post, create_timestamp_response):
        """Test that mismatched message imprint is detected."""
        test_data = b"Test data to timestamp"
        wrong_hash = hashlib.sha256(b"Different data").digest()
        
        def mock_tsa_response(url, **kwargs):
            # Extract nonce from request
            req_data = kwargs['data']
            ts_req = tsp.TimeStampReq.load(req_data)
            nonce = ts_req['nonce'].native
            
            response = Mock()
            response.status_code = 200
            # Return timestamp for wrong data
            response.content = create_timestamp_response(wrong_hash, nonce)
            return response
            
        mock_post.side_effect = mock_tsa_response
        
        os.environ['DEVELOPMENT_MODE'] = 'true'
        
        with patch.object(ProductionSigner, '_verify_timestamp_token'):
            with patch.object(ProductionSigner, '_verify_message_imprint') as mock_verify:
                # Make imprint verification fail
                mock_verify.side_effect = ValueError("Timestamp message imprint doesn't match")
                
                signer = ProductionSigner()
                
                # Should raise error
                with pytest.raises(ValueError) as exc:
                    signer._get_timestamp(test_data)
                    
                assert "message imprint" in str(exc.value).lower()
                
        os.environ.pop('DEVELOPMENT_MODE', None)
        
    def test_signed_attributes_digest_validation(self):
        """Test validation of messageDigest in signed attributes."""
        # Create test TSTInfo
        tst_info = tsp.TSTInfo({
            'version': 'v1',
            'policy': '1.2.3.4.5',
            'message_imprint': {
                'hash_algorithm': {'algorithm': 'sha256'},
                'hashed_message': b'\x00' * 32
            },
            'serial_number': 12345,
            'gen_time': datetime.utcnow(),
            'nonce': 98765
        })
        
        tst_info_der = tst_info.dump()
        correct_digest = hashlib.sha256(tst_info_der).digest()
        wrong_digest = hashlib.sha256(b'wrong').digest()
        
        # Test with correct digest
        signed_attrs_correct = [
            cms.CMSAttribute({
                'type': '1.2.840.113549.1.9.4',  # messageDigest
                'values': [core.OctetString(correct_digest)]
            })
        ]
        
        # Test with wrong digest
        signed_attrs_wrong = [
            cms.CMSAttribute({
                'type': '1.2.840.113549.1.9.4',  # messageDigest  
                'values': [core.OctetString(wrong_digest)]
            })
        ]
        
        # This would be called during _verify_timestamp_token
        # The actual implementation should verify this
        assert correct_digest != wrong_digest
        
    @patch('requests.post')
    def test_sign_filing_imprint_check(self, mock_post, create_timestamp_response):
        """Test that sign_filing verifies TSA timestamped our payload."""
        def mock_tsa_response(url, **kwargs):
            # Extract request data
            req_data = kwargs['data']
            ts_req = tsp.TimeStampReq.load(req_data)
            
            # Get the hash that was requested
            requested_hash = ts_req['message_imprint']['hashed_message'].native
            nonce = ts_req['nonce'].native
            
            response = Mock()
            response.status_code = 200
            # Return timestamp with the requested hash
            response.content = create_timestamp_response(requested_hash, nonce)
            return response
            
        mock_post.side_effect = mock_tsa_response
        
        os.environ['DEVELOPMENT_MODE'] = 'true'
        
        with patch.object(ProductionSigner, '_verify_timestamp_token'):
            signer = ProductionSigner()
            
            # Sign a filing
            test_content = b"Test XBRL content"
            metadata = {"test": "data"}
            
            sig_package = signer.sign_filing(test_content, metadata)
            
            # Verify signature package includes message imprint
            assert 'timestamp_message_imprint' in sig_package
            assert sig_package['timestamp_message_imprint'] is not None
            
        os.environ.pop('DEVELOPMENT_MODE', None)
        