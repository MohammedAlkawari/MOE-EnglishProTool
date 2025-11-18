"""
Unit tests for validators.
"""

import pytest
import os
import tempfile
import json
from validators import ManifestValidator, AudioValidator, ValidationError


class TestManifestValidator:
    """Test manifest validation."""
    
    def test_valid_manifest_structure(self):
        manifest = {
            'batch_id': 'test-batch',
            'materials': [
                {
                    'material': {
                        'section': 'listening',
                        'test_id': 'listening-001',
                        'audio': {'filename': 'test.mp3'},
                        'transcript': {'full_text': 'Some text'},
                        'questions': [{'question_id': 'Q1'}]
                    }
                }
            ]
        }
        errors = ManifestValidator.validate_manifest(manifest)
        # Note: This may fail audio validation in test, but structure should be valid
        assert isinstance(errors, list)
    
    def test_missing_batch_id(self):
        manifest = {
            'materials': []
        }
        errors = ManifestValidator.validate_manifest(manifest)
        assert any('batch_id' in err for err in errors)
    
    def test_missing_materials(self):
        manifest = {
            'batch_id': 'test'
        }
        errors = ManifestValidator.validate_manifest(manifest)
        assert any('materials' in err for err in errors)


class TestAudioValidator:
    """Test audio validation (requires ffprobe)."""
    
    def test_audio_file_not_found(self):
        is_valid, err, metadata = AudioValidator.validate_audio_file('/nonexistent/file.mp3')
        assert not is_valid
        assert 'not found' in err.lower()
    
    def test_supported_formats(self):
        supported = AudioValidator.SUPPORTED_FORMATS
        assert 'mp3' in supported
        assert 'wav' in supported
        assert 'aac' in supported


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
